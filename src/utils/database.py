import mysql.connector
from mysql.connector import Error


class Connector:
    def __init__(self):
        """Установка соединения с базой данных"""
        try:
            self.con = mysql.connector.connect(
                host='localhost',
                user='root',
                password='UM8$7I9o',
                database='test_exam'
            )
            self.cur = self.con.cursor(buffered=True, dictionary=True)

            if self.con.is_connected():
                print("Успешное подключение к базе данных")

        except Error as e:
            print(f"Ошибка подключения к базе данных: {e}")

    def disconnect(self):
        """Закрытие соединения с базой данных"""
        if self.con and self.con.is_connected():
            self.con.close()
            print("Соединение с базой данных закрыто")


class Database(Connector):
    def auth_user(self, email, password):
        """Авторизация пользователя"""
        # Проверяем в таблице модераторы
        self.cur.execute("""SELECT * FROM модераторы WHERE почта = %s AND пароль = %s""",
                         (email, password))
        user = self.cur.fetchone()

        if user:
            return {"role": "moderator", "data": user}

        # Проверяем организаторов
        self.cur.execute("""SELECT * FROM организаторы WHERE почта = %s AND пароль = %s""",
                         (email, password))
        user = self.cur.fetchone()

        if user:
            return {"role": "organizer", "data": user}

        # Проверяем участников
        self.cur.execute("""SELECT * FROM участники WHERE почта = %s AND пароль = %s""",
                         (email, password))
        user = self.cur.fetchone()

        if user:
            return {"role": "participant", "data": user}

        return None

    def get_events(self):
        """Получение всех мероприятий из базы данных"""
        try:
            # Предполагаем, что таблица называется 'мероприятия'
            self.cur.execute("""SELECT * FROM мероприятия_it ORDER BY DATE""")
            events = self.cur.fetchall()
            return events
        except Error as e:
            print(f"Ошибка при получении мероприятий: {e}")
            # Если таблица имеет другое имя, попробуем найти её
            return self._find_events_table()

    def _find_events_table(self):
        """Поиск таблицы с мероприятиями"""
        try:
            self.cur.execute("SHOW TABLES")
            tables = self.cur.fetchall()
            for table in tables:
                table_name = list(table.values())[0]
                if 'мероприят' in table_name.lower() or 'событ' in table_name.lower() or 'event' in table_name.lower():
                    self.cur.execute(f"SELECT * FROM {table_name}")
                    return self.cur.fetchall()
        except Error as e:
            print(f"Ошибка при поиске таблицы: {e}")
        return []

    def get_event_by_id(self, event_id):
        """Получение мероприятия по ID"""
        try:
            self.cur.execute("""SELECT * FROM мероприятия_it WHERE `№` = %s""", (event_id,))
            return self.cur.fetchone()
        except Error as e:
            print(f"Ошибка при получении мероприятия: {e}")
            return None

    def get_organizer_by_id(self, organizer_id):
        """Получение информации об организаторе по ID"""
        try:
            self.cur.execute("""SELECT имя, почта FROM организаторы WHERE id = %s""", (organizer_id,))
            return self.cur.fetchone()
        except Error as e:
            print(f"Ошибка при получении организатора: {e}")
            return {"имя": "Неизвестно", "почта": "Нет данных"}

