import json
from pathlib import Path
from typing import Any

from .database import Database
from .errors import (
    TableNotFoundError,
    DuplicateTableError,
    EmptyTableNameError,
    EmptyColumnsError,
    InvalidRecordLengthError,
    ColumnNotFoundError,
    InvalidColumnNameError,
    FileOperationError,
    InvalidFileFormatError,
)


class FileDatabase(Database):

    def __init__(self, directory: str = "data"):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def _get_table_path(self, table_name: str) -> Path:
        return self.directory / f"{table_name}.json"

    def _load_table(self, table_name: str) -> dict:
        path = self._get_table_path(table_name)
        if not path.exists():
            raise TableNotFoundError(f"Таблица '{table_name}' не найдена")

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            raise FileOperationError(f"Ошибка чтения файла {table_name}: {e}")

        if not isinstance(data, dict):
            raise InvalidFileFormatError(f"Файл {table_name} не является словарём")
        if "columns" not in data:
            raise InvalidFileFormatError(f"В файле {table_name} отсутствует поле 'columns'")
        if "records" not in data:
            raise InvalidFileFormatError(f"В файле {table_name} отсутствует поле 'records'")

        return data

    def _save_table(self, table_name: str, data: dict) -> None:
        path = self._get_table_path(table_name)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError as e:
            raise FileOperationError(f"Ошибка записи файла {table_name}: {e}")


    def create_table(self, table_name: str, columns: list[str]) -> None:
        table_name = table_name.strip()

        if not table_name:
            raise EmptyTableNameError("Имя таблицы не может быть пустым")
        if not columns:
            raise EmptyColumnsError("Таблица должна содержать хотя бы одну колонку")
        if len(columns) != len(set(columns)):
            raise InvalidColumnNameError("Названия колонок не должны повторяться")

        path = self._get_table_path(table_name)
        if path.exists():
            raise DuplicateTableError(f"Таблица '{table_name}' уже существует")

        data = {"columns": columns, "records": []}
        self._save_table(table_name, data)

    def list_tables(self) -> list[str]:
        return [path.stem for path in self.directory.glob("*.json")]

    def get_columns(self, table_name: str) -> list[str]:
        data = self._load_table(table_name)
        return data["columns"].copy()

    def table_exists(self, table_name: str) -> bool:
        return self._get_table_path(table_name).exists()

    def insert_record(self, table_name: str, record: tuple[Any, ...]) -> None:
        data = self._load_table(table_name)
        columns = data["columns"]

        if len(record) != len(columns):
            raise InvalidRecordLengthError(
                f"Запись должна содержать {len(columns)} полей"
            )

        record_dict = dict(zip(columns, record))
        data["records"].append(record_dict)
        self._save_table(table_name, data)

    def select_records(self, table_name: str, **filters: Any) -> list[tuple[Any, ...]]:
        data = self._load_table(table_name)
        columns = data["columns"]
        records = data["records"]

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
        data = self._load_table(table_name)
        columns = data["columns"]
        records = data["records"]

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

        if updated > 0:
            self._save_table(table_name, data)

        return updated

    def delete_records(self, table_name: str, **filters: Any) -> int:
        data = self._load_table(table_name)
        records = data["records"]

        if not filters:
            deleted = len(records)
            data["records"] = []
        else:
            to_keep = []
            deleted = 0
            for record in records:
                if self._record_matches(record, filters):
                    deleted += 1
                else:
                    to_keep.append(record)
            data["records"] = to_keep

        if deleted > 0:
            self._save_table(table_name, data)

        return deleted

    def delete_table(self, table_name: str) -> None:
        path = self._get_table_path(table_name)
        if not path.exists():
            raise TableNotFoundError(f"Таблица '{table_name}' не найдена")
        try:
            path.unlink()
        except OSError as e:
            raise FileOperationError(f"Ошибка удаления файла {table_name}: {e}")

    def clear_table(self, table_name: str) -> None:
        data = self._load_table(table_name)
        data["records"] = []
        self._save_table(table_name, data)

    def rename_table(self, old_name: str, new_name: str) -> None:
        old_name = old_name.strip()
        new_name = new_name.strip()

        if not old_name or not new_name:
            raise EmptyTableNameError("Имя таблицы не может быть пустым")

        old_path = self._get_table_path(old_name)
        new_path = self._get_table_path(new_name)

        if not old_path.exists():
            raise TableNotFoundError(f"Таблица '{old_name}' не найдена")
        if new_path.exists():
            raise DuplicateTableError(f"Таблица '{new_name}' уже существует")

        try:
            old_path.rename(new_path)
        except OSError as e:
            raise FileOperationError(f"Ошибка переименования файла: {e}")

    def rename_column(self, table_name: str, old_column: str, new_column: str) -> None:
        data = self._load_table(table_name)
        columns = data["columns"]

        if old_column not in columns:
            raise ColumnNotFoundError(f"Колонка '{old_column}' не найдена")
        if new_column in columns:
            raise ColumnNotFoundError(f"Колонка '{new_column}' уже существует")

        idx = columns.index(old_column)
        columns[idx] = new_column

        for record in data["records"]:
            if old_column in record:
                record[new_column] = record.pop(old_column)

        self._save_table(table_name, data)

    def sort_records(self, table_name: str, column: str, reverse: bool = False) -> list[tuple[Any, ...]]:
        data = self._load_table(table_name)
        columns = data["columns"]
        records = data["records"]

        if column not in columns:
            raise ColumnNotFoundError(f"Колонка '{column}' не найдена")

        tuples = [tuple(record.get(col) for col in columns) for record in records]
        col_idx = columns.index(column)
        return sorted(tuples, key=lambda x: x[col_idx], reverse=reverse)


