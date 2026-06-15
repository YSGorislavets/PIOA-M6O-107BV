import sys
from src.db.backend.memory import MemoryDatabase
from src.db.backend.file import FileDatabase
from src.db.backend.csv import CSVDatabase
from src.db.backend.errors import (
    TableNotFoundError,
    ColumnNotFoundError,
    ValidationError,
    RecordNotFoundError
)


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
        print("1. Добавить запись")
        print("2. Показать все записи")
        print("3. Поиск с фильтрацией")
        print("4. Обновить записи по фильтру")
        print("5. Удалить записи по фильтру")
        print("6. Сортировать записи")
        print("0. Выход")

    def _get_db_type_name(self):
        if isinstance(self.db, FileDatabase):
            return "File (JSON)"
        elif isinstance(self.db, CSVDatabase):
            return "File (CSV)"
        else:
            return "In-Memory"

    def _parse_filters(self, filter_str: str) -> dict:
        filters = {}
        if filter_str:
            for item in filter_str.split():
                if '=' in item:
                    key, val = item.split('=', 1)
                    filters[key.strip()] = val.strip()
                else:
                    print(f"Пропущен некорректный фильтр: {item}")
        return filters

    def _print_records(self, records, columns):
        if not records:
            print("Нет записей")
            return

        # Формируем заголовок
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
        print("\nВСЕ ЗАПИСИ")
        records = self.db.select_records(self._current_table)
        columns = self.db.get_columns(self._current_table)
        self._print_records(records, columns)

    def search_records(self):
        print("\nПОИСК С ФИЛЬТРАЦИЕЙ")
        print("Введите фильтры в формате: колонка=значение (через пробел)")
        print("Пример: student_name=Иван group=М-101")
        print("Оставьте пустым для показа всех записей")

        filter_str = input("Фильтры: ").strip()
        filters = self._parse_filters(filter_str)

        records = self.db.select_records(self._current_table, **filters)
        columns = self.db.get_columns(self._current_table)

        if not records:
            print("Записей не найдено")
        else:
            print(f"\nНайдено записей: {len(records)}")
            self._print_records(records, columns)

    def update_records(self):
        print("\nОБНОВЛЕНИЕ ЗАПИСЕЙ ПО ФИЛЬТРУ")

        # Сначала показываем все записи
        all_records = self.db.select_records(self._current_table)
        columns = self.db.get_columns(self._current_table)

        if not all_records:
            print("Нет записей для обновления")
            return

        print("\nТекущие записи:")
        self._print_records(all_records, columns)

        print("\nВведите фильтр для поиска записей, которые нужно обновить:")
        print("Формат: колонка=значение (через пробел)")
        print("Пример: student_name=Иван")
        filter_str = input("Фильтр: ").strip()

        if not filter_str:
            print("Фильтр не может быть пустым")
            return

        filters = self._parse_filters(filter_str)

        records_to_update = self.db.select_records(self._current_table, **filters)
        if not records_to_update:
            print("Записей по указанному фильтру не найдено")
            return

        print(f"\nНайдено записей для обновления: {len(records_to_update)}")
        self._print_records(records_to_update, columns)

        print("\nВведите ЧТО обновлять (колонка=значение, через пробел)")
        print("Пример: grade=5 homework_done=True")
        updates_str = input("Обновления: ").strip()

        if not updates_str:
            print("Нет данных для обновления")
            return

        updates = self._parse_filters(updates_str)

        # Проверка оценки
        if "grade" in updates:
            try:
                grade_val = int(updates["grade"])
                if not 0 <= grade_val <= 5:
                    raise ValidationError("Оценка должна быть от 0 до 5")
                updates["grade"] = grade_val
            except ValueError:
                print("Ошибка: Оценка должна быть числом")
                return

        confirm = input(f"\nОбновить {len(records_to_update)} запись(ей)? (д/н): ").strip().lower()
        if confirm not in ('д', 'да', 'y', 'yes'):
            print("Обновление отменено")
            return

        try:
            updated = self.db.update_records(self._current_table, updates, **filters)
            print(f"Обновлено {updated} записей")
        except ColumnNotFoundError as e:
            print(f"Ошибка: {e}")

    def delete_records(self):
        print("\nУДАЛЕНИЕ ЗАПИСЕЙ ПО ФИЛЬТРУ")

        # Сначала показываем все записи
        all_records = self.db.select_records(self._current_table)
        columns = self.db.get_columns(self._current_table)

        if not all_records:
            print("Нет записей для удаления")
            return

        print("\nТекущие записи:")
        self._print_records(all_records, columns)

        print("\nВведите фильтр для удаления записей:")
        print("Формат: колонка=значение (через пробел)")
        print("Пример: student_name=Иван")
        print("Для удаления всех записей введите: all")

        filter_str = input("Фильтр: ").strip()

        if not filter_str:
            print("Фильтр не может быть пустым. Для удаления всех используйте 'all'")
            return

        if filter_str.lower() == 'all':
            # Удаляем все записи
            records_to_delete = all_records
        else:
            filters = self._parse_filters(filter_str)
            records_to_delete = self.db.select_records(self._current_table, **filters)

        if not records_to_delete:
            print("Записей по указанному фильтру не найдено")
            return

        print(f"\nНайдено записей для удаления: {len(records_to_delete)}")
        self._print_records(records_to_delete, columns)

        confirm = input(f"\nУдалить {len(records_to_delete)} запись(ей)? (д/н): ").strip().lower()
        if confirm not in ('д', 'да', 'y', 'yes'):
            print("Удаление отменено")
            return

        if filter_str.lower() == 'all':
            self.db.clear_table(self._current_table)
            print(f"Удалено {len(records_to_delete)} записей (все)")
        else:
            filters = self._parse_filters(filter_str)
            deleted = self.db.delete_records(self._current_table, **filters)
            print(f"Удалено {deleted} записей")

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

    def run(self):
        print("Добро пожаловать в систему учёта посещений занятий по матану!")

        actions = {
            '1': self.add_record,
            '2': self.show_all,
            '3': self.search_records,
            '4': self.update_records,
            '5': self.delete_records,
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


