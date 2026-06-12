import sys
from src.db.backend.memory import MemoryDatabase
from src.db.backend.file import FileDatabase
from src.db.backend.csv import CSVDatabase
from src.db.backend.errors import RecordNotFoundError, ValidationError, ColumnNotFoundError


class AttendanceApp:
    def __init__(self, db_type="memory"):
        if db_type == "file":
            self.db = FileDatabase("data")
        elif db_type == "csv":
            self.db = CSVDatabase("csv_data")
        else:
            self.db = MemoryDatabase()
        self._current_table = None
        self._init_tables()

    def _init_tables(self):
        table_name = "attendance"
        columns = ["student_name", "group", "date", "topic", "is_present", "homework_done", "grade"]

        if not self.db.table_exists(table_name):
            self.db.create_table(table_name, columns)
        self._current_table = table_name

    def _print_menu(self):
        print("   УЧЁТ ПОСЕЩЕНИЙ ЗАНЯТИЙ ПО МАТАНУ")
        print(f"Тип БД: {self._get_db_type_name()}")
        print(f"Текущая таблица: {self._current_table}")
        print("1. Добавить запись о посещении")
        print("2. Показать все записи")
        print("3. Поиск с фильтрацией")
        print("4. Обновить запись")
        print("5. Удалить запись")
        print("6. Сортировать записи")
        print("0. Выход")

    def _get_db_type_name(self):
        if isinstance(self.db, FileDatabase):
            return "File (JSON)"
        elif isinstance(self.db, CSVDatabase):
            return "File (CSV)"
        else:
            return "In-Memory"

    def add_record(self):
        print("\nДОБАВЛЕНИЕ ЗАПИСИ")
        try:
            name = input("ФИО студента: ").strip()
            if not name:
                raise ValidationError("ФИО не может быть пустым")

            group = input("Номер группы: ").strip()
            if not group:
                raise ValidationError("Номер группы не может быть пустым")

            date = input("Дата занятия (ГГГГ-ММ-ДД): ").strip()
            if not date:
                raise ValidationError("Дата не может быть пустой")

            topic = input("Тема занятия: ").strip()
            if not topic:
                raise ValidationError("Тема не может быть пустой")

            is_present = input("Присутствовал? (да/нет): ").strip().lower()
            if is_present not in ['да', 'нет']:
                raise ValidationError("Введите 'да' или 'нет'")

            homework = input("Домашняя работа сделана? (да/нет): ").strip().lower()
            if homework not in ['да', 'нет']:
                raise ValidationError("Введите 'да' или 'нет'")

            grade = input("Оценка (0-5): ").strip()
            if grade:
                grade = int(grade)
                if not 0 <= grade <= 5:
                    raise ValidationError("Оценка должна быть от 0 до 5")
            else:
                grade = None

            columns = self.db.get_columns(self._current_table)
            values = [name, group, date, topic, is_present == 'да', homework == 'да', grade]

            self.db.insert_record(self._current_table, tuple(values))
            print(f"Запись добавлена!")

        except (ValidationError, ValueError) as e:
            print(f"Ошибка: {e}")

    def show_all(self):
        print("\n--- ВСЕ ЗАПИСИ ---")
        records = self.db.select_records(self._current_table)
        columns = self.db.get_columns(self._current_table)

        if not records:
            print("Нет записей")
            return

        self._print_records(records, columns)

    def search_records(self):
        print("\nПОИСК С ФИЛЬТРАЦИЕЙ")
        print("Оставьте поле пустым, чтобы не учитывать его")
        print("Формат фильтра: колонка=значение (через пробел)")
        print("Пример: student_name=Иван group=М-101")

        filter_str = input("Фильтры: ").strip()
        filters = {}

        if filter_str:
            for item in filter_str.split():
                if '=' in item:
                    key, val = item.split('=', 1)
                    filters[key.strip()] = val.strip()
                else:
                    print(f"Пропущен некорректный фильтр: {item}")

        records = self.db.select_records(self._current_table, **filters)
        columns = self.db.get_columns(self._current_table)

        if not records:
            print("Записей не найдено")
        else:
            self._print_records(records, columns)

    def update_record(self):
        print("\nОБНОВЛЕНИЕ ЗАПИСИ")
        try:
            records = self.db.select_records(self._current_table)
            columns = self.db.get_columns(self._current_table)

            if not records:
                print("Нет записей для обновления")
                return

            print("\nСуществующие записи:")
            self._print_records(records, columns)

            record_id = int(input("\nВведите ID записи для обновления: "))

            print("\nВведите новые значения (оставьте пустым, чтобы не менять):")

            updates = {}
            name = input("Новое ФИО: ").strip()
            if name:
                updates["student_name"] = name
            group = input("Новая группа: ").strip()
            if group:
                updates["group"] = group
            date = input("Новая дата: ").strip()
            if date:
                updates["date"] = date
            topic = input("Новая тема: ").strip()
            if topic:
                updates["topic"] = topic
            present = input("Присутствовал? (да/нет): ").strip().lower()
            if present and present in ['да', 'нет']:
                updates["is_present"] = present == 'да'
            homework = input("ДЗ сделана? (да/нет): ").strip().lower()
            if homework and homework in ['да', 'нет']:
                updates["homework_done"] = homework == 'да'
            grade = input("Новая оценка (0-5): ").strip()
            if grade:
                try:
                    grade_val = int(grade)
                    if not 0 <= grade_val <= 5:
                        raise ValidationError("Оценка должна быть от 0 до 5")
                    updates["grade"] = grade_val
                except ValueError:
                    print("Ошибка: Оценка должна быть числом")
                    return

            if updates:
                self.db.update_records(self._current_table, updates)
                print("Запись обновлена")
            else:
                print("Нет изменений")

        except (ValueError, RecordNotFoundError) as e:
            print(f"Ошибка: {e}")

    def delete_record(self):
        print("\nУДАЛЕНИЕ ЗАПИСИ")
        try:
            record_id = int(input("ID записи для удаления: "))
            print("В новой версии удаление работает по фильтру. Удаление отменено.")
            confirm = input("Удалить ВСЕ записи? (д/н): ").strip().lower()
            if confirm in ('д', 'да', 'y', 'yes'):
                self.db.clear_table(self._current_table)
                print("Все записи удалены")
        except (ValueError, RecordNotFoundError) as e:
            print(f"Ошибка: {e}")

    def sort_records(self):
        print("\nСОРТИРОВКА ЗАПИСЕЙ")
        columns = self.db.get_columns(self._current_table)
        records = self.db.select_records(self._current_table)

        if not records:
            print("Нет записей для сортировки")
            return

        print("Доступные поля:", ", ".join(columns))
        sort_by = input("Введите поле для сортировки: ").strip()
        if sort_by not in columns:
            print("Неверное поле")
            return

        direction = input("По возрастанию? (да/нет): ").strip().lower()
        reverse = direction != 'да'

        try:
            sorted_records = self.db.sort_records(self._current_table, sort_by, reverse)
            self._print_records(sorted_records, columns)
        except ColumnNotFoundError as e:
            print(f"Ошибка: {e}")

    def _print_records(self, records, columns):
        if not records:
            print("Нет записей")
            return

        header = ""
        for col in columns:
            header += f"{col:<20} "
        print("\n" + header)
        print("-" * (20 * len(columns)))

        for record in records:
            row = ""
            for val in record:
                val_str = str(val) if val is not None else "-"
                row += f"{val_str:<20} "
            print(row)

    def run(self):
        print("Добро пожаловать в систему учёта посещений занятий по матану!")

        actions = {
            '1': self.add_record,
            '2': self.show_all,
            '3': self.search_records,
            '4': self.update_record,
            '5': self.delete_record,
            '6': self.sort_records,
        }

        while True:
            self._print_menu()
            choice = input("Выберите действие: ").strip()

            if choice == '0':
                print("До свидания!")
                sys.exit(0)
            elif choice in actions:
                actions[choice]()
            else:
                print("Неверный выбор")


def select_database_type():
    print("\nВЫБОР ТИПА БАЗЫ ДАННЫХ")
    print("1. In-Memory (данные не сохраняются)")
    print("2. File Database (JSON, данные сохраняются в data/)")
    print("3. CSV Database (данные сохраняются в csv_data/)")
    choice = input("Выберите (1/2/3): ").strip()

    if choice == "2":
        return "file"
    elif choice == "3":
        return "csv"
    else:
        return "memory"


def main():
    db_type = select_database_type()
    app = AttendanceApp(db_type=db_type)
    app.run()


if __name__ == "__main__":
    main()
