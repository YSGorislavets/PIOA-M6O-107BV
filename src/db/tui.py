import sys
from src.db.backend.memory import Table
from src.db.backend.errors import RecordNotFoundError, ValidationError


class AttendanceApp:
    def __init__(self):
        self.table = Table()

    def _print_menu(self):
        print("   УЧЁТ ПОСЕЩЕНИЙ ЗАНЯТИЙ ПО МАТАНУ")
        print("1. Добавить запись о посещении")
        print("2. Показать все записи")
        print("3. Поиск с фильтрацией")
        print("4. Обновить запись")
        print("5. Удалить запись")
        print("6. Сортировать записи")
        print("0. Выход")

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

            record = self.table.insert({
                "student_name": name,
                "group": group,
                "date": date,
                "topic": topic,
                "is_present": is_present == 'да',
                "homework_done": homework == 'да',
                "grade": grade
            })
            print(f"Запись добавлена! ID: {record['id']}")
        except (ValidationError, ValueError) as e:
            print(f"Ошибка: {e}")

    def show_all(self):

        print("\n--- ВСЕ ЗАПИСИ ---")
        records = self.table.get_all()

        if not records:
            print("Нет записей")
            return

        self._print_records(records)

    def search_records(self):

        print("\nПОИСК ")
        print("Оставьте поле пустым, чтобы не учитывать его")

        filters = {}

        name = input("ФИО студента: ").strip()
        if name:
            filters["student_name"] = name

        group = input("Номер группы: ").strip()
        if group:
            filters["group"] = group

        date = input("Дата занятия: ").strip()
        if date:
            filters["date"] = date

        topic = input("Тема занятия: ").strip()
        if topic:
            filters["topic"] = topic

        present = input("Присутствовал? (да/нет): ").strip().lower()
        if present:
            if present not in ['да', 'нет']:
                print("Неверный ввод, пропускаем фильтр")
            else:
                filters["is_present"] = present == 'да'

        records = self.table.get_all(filters if filters else None)

        if not records:
            print("Записей не найдено")
        else:
            self._print_records(records)

    def update_record(self):

        print("\nОБНОВЛЕНИЕ ЗАПИСИ")
        try:
            record_id = int(input("ID записи для обновления: "))
            self.table.get_by_id(record_id)

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
            if present:
                if present not in ['да', 'нет']:
                    print("Неверный ввод")
                else:
                    updates["is_present"] = present == 'да'

            homework = input("ДЗ сделана? (да/нет): ").strip().lower()
            if homework:
                if homework not in ['да', 'нет']:
                    print("Неверный ввод")
                else:
                    updates["homework_done"] = homework == 'да'

            grade = input("Новая оценка (0-5): ").strip()
            if grade:
                updates["grade"] = int(grade)

            if updates:
                self.table.update(record_id, updates)
                print("Запись обновлена")
            else:
                print("Нет изменений")

        except (ValueError, RecordNotFoundError) as e:
            print(f"Ошибка: {e}")

    def delete_record(self):

        print("\nУДАЛЕНИЕ ЗАПИСИ ")
        try:
            record_id = int(input("ID записи для удаления: "))
            self.table.delete(record_id)
            print(" Запись удалена")
        except (ValueError, RecordNotFoundError) as e:
            print(f" Ошибка: {e}")

    def sort_records(self):

        print("\nСОРТИРОВКА ЗАПИСЕЙ")
        records = self.table.get_all()
        if not records:
            print("Нет записей для сортировки")
            return

        # Берём ключи из первой записи (исключая id)
        sample = records[0]
        fields = [k for k in sample.keys() if k != 'id']
        if not fields:
            print("Нет полей для сортировки")
            return

        print("Доступные поля:", ", ".join(fields))
        sort_by = input("Введите поле для сортировки: ").strip()
        if sort_by not in fields:
            print("Неверное поле")
            return

        direction = input("По возрастанию? (да/нет): ").strip().lower()
        reverse = direction != 'да'

        sorted_records = self.table.get_all(sort_by=sort_by, reverse=reverse)
        self._print_records(sorted_records)

    def _print_records(self, records):

        print(
            f"\n{'ID':<4} {'ФИО':<20} {'Группа':<8} {'Дата':<12} {'Тема':<20} {'Присутствие':<12} {'ДЗ':<4} {'Оценка':<6}")
        print("-" * 95)
        for r in records:
            present = "Да" if r['is_present'] else "Нет"
            homework = "Да" if r['homework_done'] else "Нет"
            grade = str(r['grade']) if r['grade'] is not None else "-"
            print(
                f"{r['id']:<4} {r['student_name']:<20} {r['group']:<8} {r['date']:<12} {r['topic']:<20} {present:<12} {homework:<4} {grade:<6}")

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
                print("До свидания")
                sys.exit(0)
            elif choice in actions:
                actions[choice]()
            else:
                print("Неверный выбор")


def main():
    app = AttendanceApp()
    app.run()


if __name__ == "__main__":
    main()

