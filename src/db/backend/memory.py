from copy import deepcopy
from typing import Any, Dict, List, Optional

from .database import Database
from .errors import (
    TableNotFoundError,
    DuplicateTableError,
    EmptyTableNameError,
    EmptyColumnsError,
    InvalidRecordLengthError,
    ColumnNotFoundError,
    InvalidColumnNameError,
)


class MemoryDatabase(Database):

    def __init__(self):
        self._tables: Dict[str, Dict] = {}  # table_name -> {"columns": list, "records": list}
        self._next_ids: Dict[str, int] = {}  # table_name -> next_id

    def _ensure_table_exists(self, table_name: str) -> None:
        if table_name not in self._tables:
            raise TableNotFoundError(f"Таблица '{table_name}' не найдена")

    def create_table(self, table_name: str, columns: list[str]) -> None:
        table_name = table_name.strip()

        if not table_name:
            raise EmptyTableNameError("Имя таблицы не может быть пустым")
        if not columns:
            raise EmptyColumnsError("Таблица должна содержать хотя бы одну колонку")
        if len(columns) != len(set(columns)):
            raise InvalidColumnNameError("Названия колонок не должны повторяться")

        if table_name in self._tables:
            raise DuplicateTableError(f"Таблица '{table_name}' уже существует")

        self._tables[table_name] = {"columns": columns.copy(), "records": []}
        self._next_ids[table_name] = 1

    def list_tables(self) -> list[str]:
        return list(self._tables.keys())

    def get_columns(self, table_name: str) -> list[str]:
        self._ensure_table_exists(table_name)
        return self._tables[table_name]["columns"].copy()

    def table_exists(self, table_name: str) -> bool:
        return table_name in self._tables

    def insert_record(self, table_name: str, record: tuple[Any, ...]) -> None:
        self._ensure_table_exists(table_name)
        columns = self._tables[table_name]["columns"]

        if len(record) != len(columns):
            raise InvalidRecordLengthError(
                f"Запись должна содержать {len(columns)} полей"
            )

        record_id = self._next_ids[table_name]
        record_dict = dict(zip(columns, record))
        record_dict["id"] = record_id
        self._tables[table_name]["records"].append(record_dict)
        self._next_ids[table_name] += 1

    def select_records(self, table_name: str, **filters: Any) -> list[tuple[Any, ...]]:
        self._ensure_table_exists(table_name)
        columns = self._tables[table_name]["columns"]
        records = self._tables[table_name]["records"]

        result = []
        for record in records:
            if not filters or self._record_matches(record, filters):
                row = tuple(record.get(col) for col in columns)
                result.append(row)

        return result

    def _record_matches(self, record: dict, filters: dict) -> bool:
        for key, value in filters.items():
            if record.get(key) != value:
                return False
        return True

    def update_records(self, table_name: str, updates: dict[str, Any], **filters: Any) -> int:
        self._ensure_table_exists(table_name)
        columns = self._tables[table_name]["columns"]
        records = self._tables[table_name]["records"]

        invalid_keys = [k for k in updates.keys() if k not in columns]
        if invalid_keys:
            raise ColumnNotFoundError(
                f"Неизвестное поле: {', '.join(invalid_keys)}. "
                f"Доступные поля: {columns}"
            )

        updated = 0
        for record in records:
            if not filters or self._record_matches(record, filters):
                for key, value in updates.items():
                    record[key] = value
                updated += 1

        return updated

    def delete_records(self, table_name: str, **filters: Any) -> int:
        self._ensure_table_exists(table_name)
        records = self._tables[table_name]["records"]

        if not filters:
            deleted = len(records)
            self._tables[table_name]["records"] = []
            return deleted

        to_keep = []
        deleted = 0
        for record in records:
            if self._record_matches(record, filters):
                deleted += 1
            else:
                to_keep.append(record)

        self._tables[table_name]["records"] = to_keep
        return deleted

    def delete_table(self, table_name: str) -> None:
        self._ensure_table_exists(table_name)
        del self._tables[table_name]
        del self._next_ids[table_name]

    def clear_table(self, table_name: str) -> None:
        self._ensure_table_exists(table_name)
        self._tables[table_name]["records"] = []
        self._next_ids[table_name] = 1

    def rename_table(self, old_name: str, new_name: str) -> None:
        old_name = old_name.strip()
        new_name = new_name.strip()

        if not old_name or not new_name:
            raise EmptyTableNameError("Имя таблицы не может быть пустым")

        if old_name not in self._tables:
            raise TableNotFoundError(f"Таблица '{old_name}' не найдена")
        if new_name in self._tables:
            raise DuplicateTableError(f"Таблица '{new_name}' уже существует")

        self._tables[new_name] = self._tables.pop(old_name)
        self._next_ids[new_name] = self._next_ids.pop(old_name)

    def rename_column(self, table_name: str, old_column: str, new_column: str) -> None:
        self._ensure_table_exists(table_name)
        columns = self._tables[table_name]["columns"]

        if old_column not in columns:
            raise ColumnNotFoundError(f"Колонка '{old_column}' не найдена")
        if new_column in columns:
            raise ColumnNotFoundError(f"Колонка '{new_column}' уже существует")

        idx = columns.index(old_column)
        columns[idx] = new_column

        for record in self._tables[table_name]["records"]:
            if old_column in record:
                record[new_column] = record.pop(old_column)

    def sort_records(self, table_name: str, column: str, reverse: bool = False) -> list[tuple[Any, ...]]:
        self._ensure_table_exists(table_name)
        columns = self._tables[table_name]["columns"]
        records = self._tables[table_name]["records"]

        if column not in columns:
            raise ColumnNotFoundError(f"Колонка '{column}' не найдена")

        sorted_records = sorted(records, key=lambda x: x.get(column), reverse=reverse)
        result = [tuple(r.get(col) for col in columns) for r in sorted_records]
        return result

    def get_all_info(self) -> dict[str, tuple[list[str], int]]:
        result = {}
        for name, table in self._tables.items():
            result[name] = (table["columns"].copy(), len(table["records"]))
        return result


