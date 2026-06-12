from copy import deepcopy
from typing import List, Dict, Optional
from src.db.backend.errors import RecordNotFoundError, ValidationError, ColumnNotFoundError


class Table:
    REQUIRED_COLUMNS = ["student_name", "group", "date", "topic", "is_present", "homework_done", "grade"]

    def __init__(self):
        self._data: Dict[int, Dict] = {}
        self._next_id = 1

    def insert(self, record: Dict) -> Dict:
        missing_fields = [field for field in self.REQUIRED_COLUMNS if field not in record]
        if missing_fields:
            raise ValidationError(f"Отсутствуют обязательные поля: {missing_fields}")

        record_copy = record.copy()
        record_copy["id"] = self._next_id
        self._data[self._next_id] = record_copy
        self._next_id += 1
        return self._data[self._next_id - 1].copy()

    def get_all(self, filters: Optional[Dict] = None,
                sort_by: Optional[str] = None,
                reverse: bool = False) -> List[Dict]:
        result = [deepcopy(record) for record in self._data.values()]

        if filters:
            filtered = []
            for record in result:
                match = True
                for key, value in filters.items():
                    if key not in record or record[key] != value:
                        match = False
                        break
                if match:
                    filtered.append(record)
            result = filtered

        if sort_by and result:
            missing = [i for i, record in enumerate(result) if sort_by not in record]
            if missing:
                raise ColumnNotFoundError(
                    f"Поле '{sort_by}' отсутствует у записи(ей) с индексами {missing}"
                )
            result.sort(key=lambda x: x[sort_by], reverse=reverse)

        return result

    def update(self, record_id: int, updates: Dict) -> Dict:
        if record_id not in self._data:
            raise RecordNotFoundError(f"Запись с id={record_id} не найдена")

        for key, value in updates.items():
            if key != "id":
                self._data[record_id][key] = value
        return self._data[record_id].copy()

    def delete(self, record_id: int) -> bool:
        if record_id not in self._data:
            raise RecordNotFoundError(f"Запись с id={record_id} не найдена")
        del self._data[record_id]
        return True

    def get_by_id(self, record_id: int) -> Dict:
        if record_id not in self._data:
            raise RecordNotFoundError(f"Запись с id={record_id} не найдена")
        return self._data[record_id].copy()

    def count(self) -> int:
        return len(self._data)

class MemoryDatabase:

    def __init__(self):
        self._table = Table()
        self._current_table = "attendance"

    def create_table(self, table_name: str, columns: list[str]) -> None:
        pass

    def list_tables(self) -> list[str]:
        return ["attendance"]

    def get_columns(self, table_name: str) -> list[str]:
        return Table.REQUIRED_COLUMNS

    def table_exists(self, table_name: str) -> bool:
        return table_name == "attendance"

    def insert_record(self, table_name: str, record: tuple) -> None:
        columns = Table.REQUIRED_COLUMNS
        record_dict = dict(zip(columns, record))
        self._table.insert(record_dict)

    def select_records(self, table_name: str, **filters) -> list[tuple]:
        records = self._table.get_all(filters if filters else None)
        result = []
        for rec in records:
            row = tuple(rec.get(col) for col in Table.REQUIRED_COLUMNS)
            result.append(row)
        return result

    def update_records(self, table_name: str, updates: dict, **filters) -> int:
        records = self._table.get_all(filters if filters else None)
        updated = 0
        for rec in records:
            self._table.update(rec["id"], updates)
            updated += 1
        return updated

    def delete_records(self, table_name: str, **filters) -> int:
        records = self._table.get_all(filters if filters else None)
        deleted = 0
        for rec in records:
            self._table.delete(rec["id"])
            deleted += 1
        return deleted

    def delete_table(self, table_name: str) -> None:
        self._table._data.clear()
        self._table._next_id = 1

    def clear_table(self, table_name: str) -> None:
        self._table._data.clear()
        self._table._next_id = 1

    def rename_table(self, old_name: str, new_name: str) -> None:
        pass

    def rename_column(self, table_name: str, old_column: str, new_column: str) -> None:
        pass

    def sort_records(self, table_name: str, column: str, reverse: bool = False) -> list[tuple]:
        records = self._table.get_all(sort_by=column, reverse=reverse)
        result = []
        for rec in records:
            row = tuple(rec.get(col) for col in Table.REQUIRED_COLUMNS)
            result.append(row)
        return result

