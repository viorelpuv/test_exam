import tkinter as tk
from tkinter import ttk, messagebox, font
from PIL import Image, ImageTk
import random
import time
from datetime import datetime
from utils.database import Database


class PuzzleCaptcha(tk.Frame):
    def __init__(self, parent, image_path, on_fail, on_success):
        super().__init__(parent)
        self.parent = parent
        self.on_success = on_success
        self.on_fail = on_fail
        self.image_path = image_path
        self.original_image = Image.open(image_path)
        self.parts = []
        self.correct_positions = []
        self.drag_data = {"widget": None, "x": 0, "y": 0}
        self.is_solved = False
        self.create_widgets()

    def create_widgets(self):
        self.canvas = tk.Canvas(self, width=300, height=300, bg="white")
        self.canvas.pack(pady=10)

        width, height = self.original_image.size
        part_width, part_height = width // 2, height // 2

        coords = [
            (0, 0, part_width, part_height),
            (part_width, 0, width, part_height),
            (0, part_height, part_width, height),
            (part_width, part_height, width, height),
        ]

        for i, box in enumerate(coords):
            part = self.original_image.crop(box)
            tk_part = ImageTk.PhotoImage(part)
            self.parts.append(tk_part)
            x = random.randint(0, 250)
            y = random.randint(0, 250)
            item = self.canvas.create_image(x, y, image=tk_part, anchor='nw')
            self.canvas.tag_bind(item, "<ButtonPress-1>", self.on_start_drag)
            self.canvas.tag_bind(item, "<B1-Motion>", self.on_drag)
            self.canvas.tag_bind(item, "<ButtonRelease-1>", self.on_drop)
            self.correct_positions.append((box[0], box[1]))

    def on_start_drag(self, event):
        item = self.canvas.find_closest(event.x, event.y)[0]
        self.drag_data["widget"] = item
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

    def on_drag(self, event):
        dx = event.x - self.drag_data["x"]
        dy = event.y - self.drag_data["y"]
        self.canvas.move(self.drag_data["widget"], dx, dy)
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

    def on_drop(self, event):
        pass

    def check_solution(self):
        correct = True
        items = list(self.canvas.find_all())

        if len(items) != 4:
            return False

        for i, item in enumerate(items):
            coords = self.canvas.coords(item)
            if len(coords) < 2:
                correct = False
                break

            x, y = coords[0], coords[1]
            target_x, target_y = self.correct_positions[i]
            if abs(x - target_x) > 20 or abs(y - target_y) > 20:
                correct = False
                break

        self.is_solved = correct
        return correct

    def verify_captcha(self):
        if self.check_solution():
            self.on_success()
            return True
        else:
            self.on_fail()
            return False

    def reset_parts(self):
        self.canvas.delete("all")
        self.parts = []
        self.original_image = Image.open(self.image_path)

        width, height = self.original_image.size
        part_width, part_height = width // 2, height // 2

        coords = [
            (0, 0, part_width, part_height),
            (part_width, 0, width, part_height),
            (0, part_height, part_width, height),
            (part_width, part_height, width, height),
        ]

        for i, box in enumerate(coords):
            part = self.original_image.crop(box)
            tk_part = ImageTk.PhotoImage(part)
            self.parts.append(tk_part)
            x = random.randint(0, 250)
            y = random.randint(0, 250)
            item = self.canvas.create_image(x, y, image=tk_part, anchor='nw')
            self.canvas.tag_bind(item, "<ButtonPress-1>", self.on_start_drag)
            self.canvas.tag_bind(item, "<B1-Motion>", self.on_drag)
            self.canvas.tag_bind(item, "<ButtonRelease-1>", self.on_drop)

        self.is_solved = False


class EventsWindow(tk.Toplevel):
    def __init__(self, parent, db, user_info):
        super().__init__(parent)
        self.parent = parent
        self.db = db
        self.user_info = user_info

        self.title(f"Мероприятия - {self.get_role_text(user_info['role'])}")
        self.geometry("800x600")
        self.configure(bg="#f0f0f0")

        self.create_widgets()
        self.load_events()

        self.center_window()

    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def get_role_text(self, role):
        role_texts = {
            'moderator': 'Модератор',
            'organizer': 'Организатор',
            'participant': 'Участник'
        }
        return role_texts.get(role, role)

    def create_widgets(self):
        # Верхняя панель
        top_frame = tk.Frame(self, bg="#2c3e50", height=60)
        top_frame.pack(fill="x")
        top_frame.pack_propagate(False)

        user_frame = tk.Frame(top_frame, bg="#2c3e50")
        user_frame.pack(side="left", padx=20)

        tk.Label(user_frame, text=f"Пользователь: {self.user_info['data'].get('имя', 'Неизвестно')}",
                 bg="#2c3e50", fg="white", font=('Arial', 12, 'bold')).pack(anchor="w")
        tk.Label(user_frame, text=f"Роль: {self.get_role_text(self.user_info['role'])}",
                 bg="#2c3e50", fg="white", font=('Arial', 10)).pack(anchor="w")

        logout_btn = tk.Button(top_frame, text="Выйти", command=self.logout,
                               bg="#e74c3c", fg="white", font=('Arial', 10),
                               padx=20, pady=5, borderwidth=0)
        logout_btn.pack(side="right", padx=20)

        # Заголовок
        title_frame = tk.Frame(self, bg="#f0f0f0")
        title_frame.pack(pady=(20, 10))

        tk.Label(title_frame, text="Список мероприятий",
                 font=('Arial', 20, 'bold'), bg="#f0f0f0").pack()

        # Контейнер для списка мероприятий
        events_container = tk.Frame(self, bg="#f0f0f0")
        events_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Canvas и Scrollbar
        canvas = tk.Canvas(events_container, bg="#f0f0f0", highlightthickness=0)
        scrollbar = ttk.Scrollbar(events_container, orient="vertical", command=canvas.yview)
        self.events_frame = tk.Frame(canvas, bg="#f0f0f0")

        self.events_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.events_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", on_mousewheel)

    def load_events(self):
        events = self.db.get_events()

        if not events:
            no_events_label = tk.Label(self.events_frame,
                                       text="На данный момент нет доступных мероприятий",
                                       font=('Arial', 14), bg="#f0f0f0", fg="#666")
            no_events_label.pack(pady=50)
            return

        for i, event in enumerate(events):
            self.create_event_card(event, i)

    def create_event_card(self, event, index):
        """Создание кликабельной карточки мероприятия"""
        card_frame = tk.Frame(self.events_frame, bg="white",
                              highlightbackground="#ddd", highlightthickness=1,
                              cursor="hand2")  # Курсор рука для кликабельности
        card_frame.pack(fill="x", pady=(0, 10), padx=5)

        # Связываем событие с карточкой
        card_frame.bind("<Button-1>", lambda e, ev=event: self.open_event_detail(ev))

        # Цвет фона
        bg_color = "#ffffff" if index % 2 == 0 else "#f8f9fa"
        card_frame.config(bg=bg_color)

        # Содержимое карточки
        content_frame = tk.Frame(card_frame, bg=bg_color)
        content_frame.pack(fill="x", padx=15, pady=15)

        # Название (кликабельное)
        title_label = tk.Label(content_frame,
                               text=event.get('Событие', 'Неизвестное мероприятие'),
                               font=('Arial', 14, 'bold'),
                               bg=bg_color,
                               anchor="w",
                               cursor="hand2",
                               fg="#2c3e50")  # Синий цвет для ссылки
        title_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
        title_label.bind("<Button-1>", lambda e, ev=event: self.open_event_detail(ev))

        # Детали
        details_frame = tk.Frame(content_frame, bg=bg_color)
        details_frame.grid(row=1, column=0, sticky="w")

        # Дата
        date = event.get('DATE', 'Дата не указана')
        date_label = tk.Label(details_frame, text=f"📅 {date}",
                              font=('Arial', 11), bg=bg_color, fg="#555")
        date_label.pack(anchor="w")
        date_label.bind("<Button-1>", lambda e, ev=event: self.open_event_detail(ev))

        # Город
        city = event.get('Город', 'Город не указан')
        city_label = tk.Label(details_frame, text=f"🏙️ {city}",
                              font=('Arial', 11), bg=bg_color, fg="#555")
        city_label.pack(anchor="w")
        city_label.bind("<Button-1>", lambda e, ev=event: self.open_event_detail(ev))

        # Кнопка "Подробнее"
        btn_frame = tk.Frame(content_frame, bg=bg_color)
        btn_frame.grid(row=0, column=1, rowspan=2, padx=(20, 0))

        details_btn = tk.Button(btn_frame, text="Подробнее →",
                                command=lambda ev=event: self.open_event_detail(ev),
                                bg="#3498db", fg="white",
                                font=('Arial', 10),
                                padx=15, pady=5,
                                cursor="hand2")
        details_btn.pack()

    def open_event_detail(self, event):
        """Открытие окна с детальной информацией о мероприятии"""
        event_id = event.get('№')  # Используем номер из таблицы
        if event_id:
            self.withdraw()  # Скрываем текущее окно
            EventDetailWindow(self, self.db, self.user_info, event_id)

    def logout(self):
        self.destroy()
        self.parent.deiconify()


class EventDetailWindow(tk.Toplevel):
    def __init__(self, parent, db, user_info, event_id):
        super().__init__(parent)
        self.parent = parent
        self.db = db
        self.user_info = user_info
        self.event_id = event_id

        # Получаем информацию о мероприятии
        self.event = self.db.get_event_by_id(event_id)
        if not self.event:
            messagebox.showerror("Ошибка", "Мероприятие не найдено!")
            self.destroy()
            return

        self.title(f"Мероприятие: {self.event.get('Событие', 'Неизвестно')}")
        self.geometry("900x600")
        self.configure(bg="#f5f5f5")

        self.create_widgets()

        # Центрируем окно
        self.center_window()

    def center_window(self):
        """Центрирование окна на экране"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def create_widgets(self):
        # Верхняя панель с названием
        top_frame = tk.Frame(self, bg="#2c3e50", height=80)
        top_frame.pack(fill="x")
        top_frame.pack_propagate(False)

        # Название мероприятия
        event_name = self.event.get('Событие', 'Неизвестное мероприятие')
        name_label = tk.Label(top_frame, text=event_name,
                              font=('Arial', 18, 'bold'),
                              bg="#2c3e50", fg="white")
        name_label.pack(side="left", padx=20, pady=20)

        # Кнопка назад
        back_btn = tk.Button(top_frame, text="← Назад",
                             command=self.go_back,
                             bg="#3498db", fg="white",
                             font=('Arial', 10, 'bold'),
                             padx=15, pady=5)
        back_btn.pack(side="right", padx=20)

        # Основной контент
        content_frame = tk.Frame(self, bg="#f5f5f5")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Левая панель (1/3 ширины) - основная информация
        left_frame = tk.Frame(content_frame, bg="white",
                              highlightbackground="#ddd", highlightthickness=1)
        left_frame.pack(side="left", fill="both", padx=(0, 20))
        left_frame.pack_propagate(False)
        left_frame.config(width=280)  # 1/3 от 900

        # Заголовок левой панели
        left_header = tk.Label(left_frame, text="Основная информация",
                               font=('Arial', 14, 'bold'),
                               bg="#3498db", fg="white",
                               pady=10)
        left_header.pack(fill="x")

        # Контейнер для информации
        info_container = tk.Frame(left_frame, bg="white")
        info_container.pack(fill="both", expand=True, padx=20, pady=20)

        # Отображаем информацию
        self.display_event_info(info_container)

        # Правая панель (2/3 ширины) - описание
        right_frame = tk.Frame(content_frame, bg="white",
                               highlightbackground="#ddd", highlightthickness=1)
        right_frame.pack(side="right", fill="both", expand=True)

        # Заголовок правой панели
        right_header = tk.Label(right_frame, text="Описание мероприятия",
                                font=('Arial', 14, 'bold'),
                                bg="#3498db", fg="white",
                                pady=10)
        right_header.pack(fill="x")

        # Текстовое поле с описанием
        description_text = self.get_event_description()

        # Создаем текстовое поле с прокруткой
        text_frame = tk.Frame(right_frame, bg="white")
        text_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Scrollbar для текста
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")

        # Текстовое поле
        self.description_text = tk.Text(text_frame,
                                        wrap="word",
                                        font=('Arial', 11),
                                        bg="white",
                                        height=15,
                                        yscrollcommand=scrollbar.set)
        self.description_text.pack(side="left", fill="both", expand=True)
        self.description_text.insert("1.0", description_text)
        self.description_text.config(state="disabled")  # Только для чтения

        scrollbar.config(command=self.description_text.yview)

        # Кнопки действий (в зависимости от роли)
        self.create_action_buttons(right_frame)

    def display_event_info(self, parent):
        """Отображение основной информации о мероприятии"""
        info_items = []

        # Дата
        date = self.event.get('DATE', 'Не указана')
        info_items.append(("📅 Дата проведения:", date))

        # Город
        city = self.event.get('Город', 'Не указан')
        info_items.append(("🏙️ Город:", city))

        # Длительность
        days = self.event.get('DAYS', 0)
        if days > 0:
            duration_text = f"{days} дней"
        else:
            duration_text = "1 день"
        info_items.append(("⏱️ Длительность:", duration_text))

        # Организатор (если есть связь с таблицей организаторов)
        organizer_id = self.event.get('организатор_id') or self.event.get('id_организатора')
        if organizer_id:
            organizer = self.db.get_organizer_by_id(organizer_id)
            org_name = organizer.get('имя', 'Неизвестный организатор')
            info_items.append(("👤 Организатор:", org_name))
        else:
            info_items.append(("👤 Организатор:", "Не указан"))

        # Место проведения (если есть поле)
        location = self.event.get('Место') or self.event.get('Локация') or self.event.get('Адрес')
        if location:
            info_items.append(("📍 Место проведения:", location))

        # Время (если есть поле)
        time_info = self.event.get('Время') or self.event.get('Время_начала')
        if time_info:
            info_items.append(("🕐 Время начала:", time_info))

        # Отображаем все пункты
        for label, value in info_items:
            item_frame = tk.Frame(parent, bg="white")
            item_frame.pack(fill="x", pady=8)

            tk.Label(item_frame, text=label,
                     font=('Arial', 11, 'bold'),
                     bg="white", fg="#333",
                     width=20, anchor="w").pack(side="left")

            tk.Label(item_frame, text=value,
                     font=('Arial', 11),
                     bg="white", fg="#555",
                     anchor="w").pack(side="left", padx=(10, 0))

    def get_event_description(self):
        """Получение описания мероприятия"""
        # Проверяем различные возможные названия полей с описанием
        possible_fields = ['Описание', 'описание', 'Description', 'description',
                           'Текст', 'текст', 'Информация', 'информация']

        for field in possible_fields:
            if field in self.event and self.event[field]:
                return self.event[field]

        # Если описания нет, создаем текст с местом и временем
        location = self.event.get('Место') or self.event.get('Локация') or self.event.get('Адрес') or 'Место не указано'
        time_info = self.event.get('Время') or self.event.get('Время_начала') or 'Время не указано'
        date = self.event.get('DATE', 'Дата не указана')

        description = f"""Мероприятие "{self.event.get('Событие', 'Неизвестное мероприятие')}"

Место проведения: {location}
Дата: {date}
Время: {time_info}
Город: {self.event.get('Город', 'Не указан')}

Дополнительная информация отсутствует."""

        return description

    def create_action_buttons(self, parent):
        """Создание кнопок действий в зависимости от роли пользователя"""
        button_frame = tk.Frame(parent, bg="white")
        button_frame.pack(fill="x", padx=20, pady=(0, 20))

        role = self.user_info['role']

        if role == 'moderator':
            # Кнопки для модератора
            tk.Button(button_frame, text="Редактировать",
                      bg="#f39c12", fg="white",
                      font=('Arial', 11, 'bold'),
                      padx=20, pady=10,
                      command=self.edit_event).pack(side="left", padx=5)

            tk.Button(button_frame, text="Удалить",
                      bg="#e74c3c", fg="white",
                      font=('Arial', 11, 'bold'),
                      padx=20, pady=10,
                      command=self.delete_event).pack(side="left", padx=5)

            tk.Button(button_frame, text="Статистика",
                      bg="#9b59b6", fg="white",
                      font=('Arial', 11, 'bold'),
                      padx=20, pady=10,
                      command=self.show_statistics).pack(side="left", padx=5)

        elif role == 'organizer':
            # Кнопки для организатора
            tk.Button(button_frame, text="Редактировать",
                      bg="#f39c12", fg="white",
                      font=('Arial', 11, 'bold'),
                      padx=20, pady=10,
                      command=self.edit_event).pack(side="left", padx=5)

            tk.Button(button_frame, text="Список участников",
                      bg="#3498db", fg="white",
                      font=('Arial', 11, 'bold'),
                      padx=20, pady=10,
                      command=self.show_participants).pack(side="left", padx=5)

        elif role == 'participant':
            # Кнопки для участника
            tk.Button(button_frame, text="Записаться",
                      bg="#2ecc71", fg="white",
                      font=('Arial', 11, 'bold'),
                      padx=30, pady=10,
                      command=self.register_for_event).pack(side="left", padx=5)

            tk.Button(button_frame, text="Поделиться",
                      bg="#3498db", fg="white",
                      font=('Arial', 11, 'bold'),
                      padx=20, pady=10,
                      command=self.share_event).pack(side="left", padx=5)

    def go_back(self):
        """Возврат к списку мероприятий"""
        self.destroy()
        self.parent.deiconify()  # Показываем родительское окно

    # Методы-заглушки для кнопок
    def edit_event(self):
        messagebox.showinfo("Редактирование", "Функция редактирования в разработке")

    def delete_event(self):
        if messagebox.askyesno("Удаление", "Вы уверены, что хотите удалить мероприятие?"):
            messagebox.showinfo("Удаление", "Мероприятие удалено (заглушка)")
            self.go_back()

    def show_statistics(self):
        messagebox.showinfo("Статистика", "Статистика мероприятия (заглушка)")

    def show_participants(self):
        messagebox.showinfo("Участники", "Список участников (заглушка)")

    def register_for_event(self):
        if messagebox.askyesno("Запись", "Записаться на мероприятие?"):
            messagebox.showinfo("Успех", "Вы успешно записались на мероприятие!")

    def share_event(self):
        messagebox.showinfo("Поделиться", "Ссылка скопирована в буфер обмена")


class OrganizerWindow(tk.Toplevel):
    def __init__(self, parent, db, user_info):
        super().__init__(parent)
        self.parent = parent
        self.db = db
        self.user_info = user_info

        # Настройка окна
        self.title("Окно организатора")
        self.geometry("1000x700")
        self.configure(bg="#f5f5f5")
        self.minsize(900, 600)

        # Создаем интерфейс
        self.create_widgets()

        # Центрируем окно
        self.center_window()

    def center_window(self):
        """Центрирование окна"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def get_greeting(self):
        """Получение приветствия в зависимости от времени"""
        current_hour = datetime.now().hour

        if 9 <= current_hour < 11:
            return "Доброе утро"
        elif 11 <= current_hour < 18:
            return "Добрый день"
        elif 18 <= current_hour <= 23:
            return "Добрый вечер"
        else:
            return "Доброй ночи"

    def get_time_range(self):
        """Получение временного диапазона"""
        current_hour = datetime.now().hour

        if 9 <= current_hour < 11:
            return "(9:00-11:00)"
        elif 11 <= current_hour < 18:
            return "(11:01-18:00)"
        elif 18 <= current_hour <= 23:
            return "(18:01-00:00)"
        else:
            return "(00:01-8:59)"

    def create_widgets(self):
        # Верхняя панель с заголовком
        top_frame = tk.Frame(self, bg="#2c3e50", height=70)
        top_frame.pack(fill="x")
        top_frame.pack_propagate(False)

        # Заголовок
        title_label = tk.Label(top_frame, text="ОКНО ОРГАНИЗАТОРА",
                               font=('Arial', 22, 'bold'),
                               bg="#2c3e50", fg="white")
        title_label.pack(side="left", padx=30, pady=20)

        # Кнопка выхода справа
        logout_btn = tk.Button(top_frame, text="Выйти",
                               command=self.logout,
                               bg="#e74c3c", fg="white",
                               font=('Arial', 11),
                               padx=20, pady=5,
                               cursor="hand2",
                               relief="flat")
        logout_btn.pack(side="right", padx=30, pady=20)

        # Основной контент
        main_frame = tk.Frame(self, bg="#f5f5f5")
        main_frame.pack(fill="both", expand=True, padx=30, pady=20)

        # Левая панель (1/4 экрана) - профиль
        left_panel = tk.Frame(main_frame, bg="white",
                              relief="solid", borderwidth=1)
        left_panel.pack(side="left", fill="y", padx=(0, 30))
        left_panel.pack_propagate(False)
        left_panel.config(width=220)  # 1/4 от 880px

        # Фото организатора
        photo_frame = tk.Frame(left_panel, bg="white", pady=40)
        photo_frame.pack(fill="x")

        # Серый квадрат для фото
        photo_canvas = tk.Canvas(photo_frame, width=150, height=150,
                                 bg="#cccccc", highlightthickness=0)
        photo_canvas.pack()

        # Текст "Фото" в центре
        photo_canvas.create_text(75, 75, text="Фото",
                                 font=("Arial", 16), fill="#666666")

        # Кнопка "Мой профиль"
        profile_btn = tk.Button(left_panel, text="Мой профиль",
                                command=self.open_profile,
                                bg="#3498db", fg="white",
                                font=("Arial", 13, "bold"),
                                width=18, height=2,
                                padx=10, pady=5)
        profile_btn.pack(pady=30)

        # Центральная панель
        center_panel = tk.Frame(main_frame, bg="#f5f5f5")
        center_panel.pack(side="left", fill="both", expand=True)

        # Центральный контейнер
        center_container = tk.Frame(center_panel, bg="white",
                                    relief="solid", borderwidth=1)
        center_container.pack(expand=True, fill="both")

        # Контейнер для центрального содержимого
        center_content = tk.Frame(center_container, bg="white")
        center_content.pack(expand=True)

        # Приветствие
        greeting = self.get_greeting()
        time_range = self.get_time_range()

        greeting_frame = tk.Frame(center_content, bg="white")
        greeting_frame.pack(pady=(50, 10))

        greeting_label = tk.Label(greeting_frame,
                                  text=greeting,
                                  font=("Arial", 28, "bold"),
                                  bg="white",
                                  fg="#2c3e50")
        greeting_label.pack()

        time_label = tk.Label(greeting_frame,
                              text=time_range,
                              font=("Arial", 14),
                              bg="white",
                              fg="#666666")
        time_label.pack(pady=(5, 0))

        # Имя пользователя
        user_name = self.user_info['data'].get('имя', 'Организатор')
        name_frame = tk.Frame(center_content, bg="white")
        name_frame.pack(pady=30)

        name_label = tk.Label(name_frame,
                              text=user_name,
                              font=("Arial", 20),
                              bg="white",
                              fg="#333333")
        name_label.pack()

        # Кнопки меню
        buttons_frame = tk.Frame(center_content, bg="white")
        buttons_frame.pack(pady=20)

        # Список кнопок
        buttons = [
            ("Мероприятия", self.open_events),
            ("Участники", self.open_participants),
            ("Жюри", self.open_jury)
        ]

        for text, command in buttons:
            btn_frame = tk.Frame(buttons_frame, bg="white")
            btn_frame.pack(pady=15)

            btn = tk.Button(btn_frame, text=text,
                            command=command,
                            bg="#2c3e50", fg="white",
                            font=("Arial", 14, "bold"),
                            width=20, height=2,
                            padx=20, pady=10,
                            cursor="hand2",
                            relief="raised")
            btn.pack()

    def open_profile(self):
        """Открытие профиля"""
        messagebox.showinfo("Профиль", "Редактирование профиля")

    def open_events(self):
        """Открытие мероприятий"""
        self.withdraw()  # Скрываем окно организатора
        EventsWindow(self, self.db, self.user_info)

    def open_participants(self):
        """Открытие участников"""
        messagebox.showinfo("Участники", "Список участников")

    def open_jury(self):
        """Открытие жюри"""
        messagebox.showinfo("Жюри", "Список жюри")

    def logout(self):
        """Выход из системы"""
        self.destroy()
        self.parent.deiconify()  # Показываем окно авторизации


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.geometry("600x850")
        self.resizable(False, False)
        self.configure(bg="#191919")
        self.locked_until = None
        self.failed_attempts = 0
        self.max_attempts = 3
        self.lock_duration = 10 * 60
        self.captcha_frame = None
        self.login_button = None
        self.captcha = None
        self.captcha_button = None
        self.current_user = None

        # База данных
        self.db = Database()

        self.show_login()

    def show_login(self):
        """Показ окна авторизации"""
        self.title('Авторизация')

        # Очищаем окно
        for widget in self.winfo_children():
            widget.destroy()

        # Создаем интерфейс авторизации
        self.create_auth_ui()

    def create_auth_ui(self):
        """Создание интерфейса авторизации"""
        title_label = tk.Label(self, text="Авторизация", font=('Arial', 20, 'bold'),
                               bg="#191919", fg="white")
        title_label.pack(pady=(20, 30))

        # Поля ввода
        login_label = tk.Label(self, text="Почта:", font=('Arial', 12),
                               bg="#191919", fg="white")
        login_label.pack(pady=(0, 5))
        self.login_entry = ttk.Entry(self, width=50, font=('Arial', 12))
        self.login_entry.pack(pady=(0, 20))
        self.login_entry.bind('<KeyRelease>', self.check_fields)

        password_label = tk.Label(self, text="Пароль:", font=('Arial', 12),
                                  bg="#191919", fg="white")
        password_label.pack(pady=(0, 5))
        self.password_entry = ttk.Entry(self, width=50, font=('Arial', 12), show="*")
        self.password_entry.pack(pady=(0, 30))
        self.password_entry.bind('<KeyRelease>', self.check_fields)

        # Капча
        captcha_label = tk.Label(self, text="Соберите пазл:",
                                 font=('Arial', 12), bg="#191919", fg="white")
        captcha_label.pack(pady=(0, 10))

        self.captcha_frame = tk.Frame(self, bg="#191919")
        self.captcha_frame.pack(pady=10)

        captcha_buttons_frame = tk.Frame(self, bg="#191919")
        captcha_buttons_frame.pack(pady=10)

        self.captcha_button = ttk.Button(captcha_buttons_frame, text="Проверить капчу",
                                         command=self.check_captcha)
        self.captcha_button.pack(side="left", padx=5)

        reset_captcha_button = ttk.Button(captcha_buttons_frame, text="Сбросить капчу",
                                          command=self.reset_captcha)
        reset_captcha_button.pack(side="left", padx=5)

        # Кнопка входа
        self.login_button = ttk.Button(self, text="Войти",
                                       command=self.attempt_login,
                                       state="disabled")
        self.login_button.pack(pady=20)

        # Счетчик попыток
        self.attempts_label = tk.Label(self, text=f"Попыток: {self.failed_attempts}/{self.max_attempts}",
                                       font=('Arial', 10), bg="#191919", fg="white")
        self.attempts_label.pack()

        # Загружаем капчу
        self.start_captcha()

    def start_captcha(self):
        """Загрузка капчи"""
        for widget in self.captcha_frame.winfo_children():
            widget.destroy()

        self.captcha = PuzzleCaptcha(self.captcha_frame,
                                     r"C:\Users\Nik\Desktop\de_test\src\i.png",
                                     self.captcha_failed,
                                     self.captcha_success)
        self.captcha.pack()

    def check_captcha(self):
        """Проверка капчи"""
        if self.captcha.verify_captcha():
            self.check_fields()
        else:
            self.check_fields()

    def reset_captcha(self):
        """Сброс капчи"""
        if self.captcha:
            self.captcha.reset_parts()
            self.check_fields()

    def captcha_success(self):
        """Успешная проверка капчи"""
        messagebox.showinfo("Успех", "Капча пройдена!")
        self.check_fields()

    def captcha_failed(self):
        """Неудачная проверка капчи"""
        self.failed_attempts += 1
        self.attempts_label.config(text=f"Попыток: {self.failed_attempts}/{self.max_attempts}")

        if self.failed_attempts >= self.max_attempts:
            self.lock_login()
        else:
            messagebox.showerror("Ошибка",
                                 f"Капча не пройдена! Осталось попыток: {self.max_attempts - self.failed_attempts}")
            self.captcha.reset_parts()

    def check_fields(self, event=None):
        """Проверка полей формы"""
        login_filled = bool(self.login_entry.get().strip())
        password_filled = bool(self.password_entry.get().strip())
        captcha_solved = self.captcha.is_solved if self.captcha else False
        is_locked = self.locked_until is not None and time.time() < self.locked_until

        if is_locked:
            self.login_button.config(state="disabled")
            self.captcha_button.config(state="disabled")
        else:
            self.captcha_button.config(state="normal")
            if login_filled and password_filled and captcha_solved:
                self.login_button.config(state="normal")
            else:
                self.login_button.config(state="disabled")

    def attempt_login(self):
        """Попытка авторизации"""
        email = self.login_entry.get().strip()
        password = self.password_entry.get().strip()

        # Проверка в базе данных
        user_data = self.db.auth_user(email, password)

        if user_data:
            self.current_user = user_data
            self.withdraw()  # Скрываем окно авторизации

            # ВАЖНОЕ ИСПРАВЛЕНИЕ: Открываем разные окна в зависимости от роли
            if user_data['role'] == 'organizer':
                self.show_organizer_window(user_data)
            elif user_data['role'] == 'moderator':
                self.show_moderator_window(user_data)
            elif user_data['role'] == 'participant':
                self.show_events_window(user_data)
        else:
            messagebox.showerror("Ошибка", "Неверная почта или пароль!")
            self.reset_captcha()

    def show_organizer_window(self, user_data):
        """Показ окна организатора"""
        OrganizerWindow(self, self.db, user_data)

    def show_moderator_window(self, user_data):
        """Показ окна модератора"""
        # Можно создать отдельное окно для модератора или использовать EventsWindow
        messagebox.showinfo("Модератор", "Добро пожаловать, модератор!")
        self.show_events_window(user_data)

    def show_events_window(self, user_data):
        """Показ окна с мероприятиями (для участников)"""
        EventsWindow(self, self.db, user_data)

    def lock_login(self):
        """Блокировка входа"""
        self.locked_until = time.time() + self.lock_duration
        messagebox.showwarning("Блокировка", "Вход заблокирован на 10 минут!")
        self.update_lock_timer()

    def update_lock_timer(self):
        """Обновление таймера блокировки"""
        if self.locked_until is not None:
            remaining = int(self.locked_until - time.time())
            if remaining > 0:
                self.after(1000, self.update_lock_timer)
            else:
                self.locked_until = None
                self.failed_attempts = 0
                self.check_fields()


if __name__ == '__main__':
    app = App()
    app.mainloop()