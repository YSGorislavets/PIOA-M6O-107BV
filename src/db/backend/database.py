from abc import ABC, abstractmethod
from typing import Any


class Database(ABC):

    @abstractmethod
    def create_table(self, table_name: str, columns: list[str]) -> None:
        pass

    @abstractmethod
    def list_tables(self) -> list[str]:
        pass

    @abstractmethod
    def get_columns(self, table_name: str) -> list[str]:
        pass

    @abstractmethod
    def insert_record(self, table_name: str, record: tuple[Any, ...]) -> None:
        pass

    @abstractmethod
    def select_records(self, table_name: str, **filters: Any) -> list[tuple[Any, ...]]:
        pass

    @abstractmethod
    def update_records(self, table_name: str, updates: dict[str, Any], **filters: Any) -> int:
        pass

    @abstractmethod
    def delete_records(self, table_name: str, **filters: Any) -> int:
        pass

    @abstractmethod
    def delete_table(self, table_name: str) -> None:
        pass

    @abstractmethod
    def clear_table(self, table_name: str) -> None:
        pass

    @abstractmethod
    def table_exists(self, table_name: str) -> bool:
        pass

    @abstractmethod
    def rename_table(self, old_name: str, new_name: str) -> None:
        pass

    @abstractmethod
    def rename_column(self, table_name: str, old_column: str, new_column: str) -> None:
        pass

    @abstractmethod
    def sort_records(self, table_name: str, column: str, reverse: bool = False) -> list[tuple[Any, ...]]:
        pass

