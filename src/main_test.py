import tkinter as tk
from tkinter import Tk, ttk, messagebox
from PIL import Image, ImageTk
import random
import time


class PuzzleCaptcha(tk.Frame):
    def __init__(self, parent, image_path, on_success):
        super().__init__(parent)
        self.parent = parent
        self.on_success = on_success
        self.image_path = image_path
        self.original_image = Image.open(image_path)
        self.parts = []
        self.correct_positions = []
        self.drag_data = {"widget": None, "x": 0, "y": 0}
        self.create_widgets()

    def create_widgets(self):
        # Создаем область для пазла
        self.canvas = tk.Canvas(self, width=300, height=300, bg="white")
        self.canvas.pack(pady=10)

        # Разделим изображение на 4 части
        width, height = self.original_image.size
        part_width, part_height = width // 2, height // 2

        coords = [
            (0, 0, part_width, part_height),
            (part_width, 0, width, part_height),
            (0, part_height, part_width, height),
            (part_width, part_height, width, height),
        ]

        # Создаем части
        for i, box in enumerate(coords):
            part = self.original_image.crop(box)
            tk_part = ImageTk.PhotoImage(part)
            self.parts.append(tk_part)
            # Создаем "слепки" на канвасе в случайных позициях
            x = random.randint(0, 250)
            y = random.randint(0, 250)
            item = self.canvas.create_image(x, y, image=tk_part, anchor='nw')
            self.canvas.tag_bind(item, "<ButtonPress-1>", self.on_start_drag)
            self.canvas.tag_bind(item, "<B1-Motion>", self.on_drag)
            self.canvas.tag_bind(item, "<ButtonRelease-1>", self.on_drop)
            self.correct_positions.append((box[0], box[1]))

        # Кнопка проверки
        self.check_button = ttk.Button(self, text="Проверить", command=self.check_solution)
        self.check_button.pack(pady=10)

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
        pass  # Можно добавить ограничения или проверки при отпускании

    def check_solution(self):
        # Проверка позиции частей
        correct = True
        items = list(self.canvas.find_all())

        # Убедимся, что порядок соответствует
        for i, item in enumerate(items):
            coords = self.canvas.coords(item)
            if len(coords) < 2:
                correct = False
                break

            x, y = coords[0], coords[1]
            # Проверяем, находится ли часть в районе правильной позиции
            target_x, target_y = self.correct_positions[i]
            if abs(x - target_x) > 20 or abs(y - target_y) > 20:
                correct = False
                break

        if correct:
            messagebox.showinfo("Успех", "Капча пройдена!")
            self.on_success()
        else:
            messagebox.showerror("Ошибка", "Пазл собран неправильно. Попробуйте снова.")
            self.reset_parts()

    def reset_parts(self):
        # Очищаем canvas
        self.canvas.delete("all")

        # Очищаем список частей
        self.parts = []

        # Загружаем изображение заново (на случай, если оно было изменено)
        self.original_image = Image.open(self.image_path)

        # Разделим изображение на 4 части
        width, height = self.original_image.size
        part_width, part_height = width // 2, height // 2

        coords = [
            (0, 0, part_width, part_height),
            (part_width, 0, width, part_height),
            (0, part_height, part_width, height),
            (part_width, part_height, width, height),
        ]

        # Создаем части
        for i, box in enumerate(coords):
            part = self.original_image.crop(box)
            tk_part = ImageTk.PhotoImage(part)
            self.parts.append(tk_part)
            # Создаем "слепки" на канвасе в случайных позициях
            x = random.randint(0, 250)
            y = random.randint(0, 250)
            item = self.canvas.create_image(x, y, image=tk_part, anchor='nw')
            self.canvas.tag_bind(item, "<ButtonPress-1>", self.on_start_drag)
            self.canvas.tag_bind(item, "<B1-Motion>", self.on_drag)
            self.canvas.tag_bind(item, "<ButtonRelease-1>", self.on_drop)


class App(Tk):
    def __init__(self):
        super().__init__()
        self.geometry("600x800")
        self.resizable(False, False)
        self.configure(bg="#191919")
        self.locked_until = None
        self.captcha_frame = None  # Добавляем атрибут для хранения ссылки на фрейм капчи
        self.show_login()

    def show_login(self):
        self.title('Авторизация')

        # Очищаем окно, если были предыдущие виджеты
        for widget in self.winfo_children():
            widget.destroy()

        self.login_entry = ttk.Entry(self, width=80, font=('Arial', 15))
        self.login_entry.pack(padx=50, pady=(50, 0))
        self.password_entry = ttk.Entry(self, width=80, font=('Arial', 15))
        self.password_entry.pack(padx=50, pady=30)

        # Создаем контейнер для капчи один раз
        self.captcha_frame = tk.Frame(self, bg="#191919")
        self.captcha_frame.pack(pady=20)

        self.start_captcha()

    def start_captcha(self):
        # Удаляем старую капчу из контейнера, если она есть
        for widget in self.captcha_frame.winfo_children():
            widget.destroy()

        # Создаем новую капчу
        def captcha_success():
            self.captcha_frame.destroy()
            self.show_main()

        self.captcha = PuzzleCaptcha(self.captcha_frame, r"C:\Users\Nik\Desktop\de_test\src\i.png", captcha_success)
        self.captcha.pack()

    def show_main(self):
        # Здесь можно добавить основной интерфейс после успешной капчи
        self.title("Основное окно")
        label = tk.Label(self, text="Вы успешно прошли капчу!", font=('Arial', 20), bg="#191919", fg="white")
        label.pack(pady=200)

    def lock_input(self, minutes=10):
        self.locked_until = time.time() + minutes * 60
        messagebox.showwarning("Блокировка", f"Вход заблокирован на {minutes} минут.")
        self.after(1000, self.check_lock)

    def check_lock(self):
        if self.locked_until and time.time() < self.locked_until:
            remaining = int(self.locked_until - time.time())
            self.after(1000, self.check_lock)
        else:
            self.locked_until = None
            # Можно разблокировать или перезапустить капчу
            self.start_captcha()


if __name__ == '__main__':
    app = App()
    app.mainloop()