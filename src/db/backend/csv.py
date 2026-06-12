import csv
import os
from pathlib import Path
from typing import Any

from src.db.backend.database import Database
from src.db.backend.errors import (
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


class CSVDatabase(Database):

    def __init__(self, directory: str = "csv_data"):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def _get_table_path(self, table_name: str) -> Path:
        return self.directory / f"{table_name}.csv"

    def _load_table(self, table_name: str) -> tuple[list[str], list[dict]]:
        path = self._get_table_path(table_name)
        if not path.exists():
            raise TableNotFoundError(f"Таблица '{table_name}' не найдена")

        try:
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                columns = reader.fieldnames or []
                records = list(reader)
                for record in records:
                    for key in record:
                        if record[key] == "True":
                            record[key] = True
                        elif record[key] == "False":
                            record[key] = False
                        elif record[key].isdigit():
                            record[key] = int(record[key])
                return columns, records
        except Exception as e:
            raise FileOperationError(f"Ошибка чтения файла {table_name}: {e}")

    def _save_table(self, table_name: str, columns: list[str], records: list[dict]) -> None:
        path = self._get_table_path(table_name)
        try:
            with open(path, "w", encoding="utf-8", newline='') as f:
                writer = csv.DictWriter(f, fieldnames=columns)
                writer.writeheader()
                writer.writerows(records)
        except Exception as e:
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

        self._save_table(table_name, columns, [])

    def list_tables(self) -> list[str]:
        return [path.stem for path in self.directory.glob("*.csv")]

    def get_columns(self, table_name: str) -> list[str]:
        columns, _ = self._load_table(table_name)
        return columns

    def table_exists(self, table_name: str) -> bool:
        return self._get_table_path(table_name).exists()

    def insert_record(self, table_name: str, record: tuple[Any, ...]) -> None:
        columns, records = self._load_table(table_name)
        if len(record) != len(columns):
            raise InvalidRecordLengthError(f"Запись должна содержать {len(columns)} полей")

        record_dict = dict(zip(columns, record))
        records.append(record_dict)
        self._save_table(table_name, columns, records)

    def select_records(self, table_name: str, **filters: Any) -> list[tuple[Any, ...]]:
        columns, records = self._load_table(table_name)
        result = []
        for record in records:
            match = True
            for key, value in filters.items():
                if record.get(key) != value:
                    match = False
                    break
            if match:
                result.append(tuple(record.get(col) for col in columns))
        return result

    def update_records(self, table_name: str, updates: dict[str, Any], **filters: Any) -> int:
        columns, records = self._load_table(table_name)
        updated = 0
        for record in records:
            match = True
            for key, value in filters.items():
                if record.get(key) != value:
                    match = False
                    break
            if match:
                for key, value in updates.items():
                    if key not in columns:
                        raise ColumnNotFoundError(f"Колонка '{key}' не найдена")
                    record[key] = value
                updated += 1
        if updated > 0:
            self._save_table(table_name, columns, records)
        return updated

    def delete_records(self, table_name: str, **filters: Any) -> int:
        columns, records = self._load_table(table_name)
        if not filters:
            deleted = len(records)
            records.clear()
        else:
            to_keep = []
            deleted = 0
            for record in records:
                match = True
                for key, value in filters.items():
                    if record.get(key) != value:
                        match = False
                        break
                if match:
                    deleted += 1
                else:
                    to_keep.append(record)
            records = to_keep
        if deleted > 0:
            self._save_table(table_name, columns, records)
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
        columns, _ = self._load_table(table_name)
        self._save_table(table_name, columns, [])

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
        columns, records = self._load_table(table_name)

        if old_column not in columns:
            raise ColumnNotFoundError(f"Колонка '{old_column}' не найдена")
        if new_column in columns:
            raise ColumnNotFoundError(f"Колонка '{new_column}' уже существует")

        idx = columns.index(old_column)
        columns[idx] = new_column

        for record in records:
            if old_column in record:
                record[new_column] = record.pop(old_column)

        self._save_table(table_name, columns, records)

    def sort_records(self, table_name: str, column: str, reverse: bool = False) -> list[tuple]:
        columns, records = self._load_table(table_name)

        if column not in columns:
            raise ColumnNotFoundError(f"Колонка '{column}' не найдена")

        sorted_records = sorted(records, key=lambda x: x.get(column), reverse=reverse)

        result = []
        for record in sorted_records:
            row = tuple(record.get(col) for col in columns)
            result.append(row)

        return result



