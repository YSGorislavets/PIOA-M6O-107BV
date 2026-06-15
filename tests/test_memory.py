import pytest
from src.db.backend.memory import MemoryDatabase
from src.db.backend.errors import (
    TableNotFoundError,
    DuplicateTableError,
    EmptyTableNameError,
    EmptyColumnsError,
    InvalidRecordLengthError,
    ColumnNotFoundError,
)


class TestMemoryDatabase:
    def setup_method(self):
        self.db = MemoryDatabase()

    def test_create_table_success(self):
        self.db.create_table("students", ["id", "name"])
        assert self.db.table_exists("students")
        assert self.db.get_columns("students") == ["id", "name"]

    def test_create_table_duplicate(self):
        self.db.create_table("students", ["id"])
        with pytest.raises(DuplicateTableError):
            self.db.create_table("students", ["id"])

    def test_create_table_empty_name(self):
        with pytest.raises(EmptyTableNameError):
            self.db.create_table("", ["id"])

    def test_create_table_no_columns(self):
        with pytest.raises(EmptyColumnsError):
            self.db.create_table("test", [])

    def test_insert_and_select(self):
        self.db.create_table("students", ["id", "name"])
        self.db.insert_record("students", (1, "Иван"))
        records = self.db.select_records("students")
        assert len(records) == 1
        assert records[0] == (1, "Иван")

    def test_select_with_filter(self):
        self.db.create_table("students", ["id", "name"])
        self.db.insert_record("students", (1, "Иван"))
        self.db.insert_record("students", (2, "Пётр"))
        records = self.db.select_records("students", name="Иван")
        assert len(records) == 1
        assert records[0][1] == "Иван"

    def test_update_records(self):
        self.db.create_table("students", ["id", "name"])
        self.db.insert_record("students", (1, "Иван"))
        self.db.update_records("students", {"name": "Анна"})
        records = self.db.select_records("students")
        assert records[0][1] == "Анна"

    def test_update_records_with_filter(self):
        self.db.create_table("students", ["id", "name"])
        self.db.insert_record("students", (1, "Иван"))
        self.db.insert_record("students", (2, "Пётр"))
        self.db.update_records("students", {"name": "Анна"}, name="Иван")
        records = self.db.select_records("students", name="Анна")
        assert len(records) == 1

    def test_delete_records_with_filter(self):
        self.db.create_table("students", ["id", "name"])
        self.db.insert_record("students", (1, "Иван"))
        self.db.insert_record("students", (2, "Пётр"))
        self.db.delete_records("students", name="Иван")
        assert len(self.db.select_records("students")) == 1

    def test_delete_table(self):
        self.db.create_table("students", ["id"])
        self.db.delete_table("students")
        assert not self.db.table_exists("students")

    def test_clear_table(self):
        self.db.create_table("students", ["id"])
        self.db.insert_record("students", (1,))
        self.db.clear_table("students")
        assert len(self.db.select_records("students")) == 0

    def test_table_not_found(self):
        with pytest.raises(TableNotFoundError):
            self.db.select_records("ghost")

    def test_sort_records(self):
        self.db.create_table("students", ["name", "age"])
        self.db.insert_record("students", ("Иван", 25))
        self.db.insert_record("students", ("Анна", 20))
        sorted_records = self.db.sort_records("students", "age", reverse=False)
        ages = [r[1] for r in sorted_records]
        assert ages == [20, 25]

    def test_get_all_info(self):
        self.db.create_table("t1", ["id", "name"])
        self.db.insert_record("t1", (1, "test"))
        self.db.create_table("t2", ["col"])
        info = self.db.get_all_info()
        assert len(info) == 2
        assert "t1" in info
        assert "t2" in info
        columns, count = info["t1"]
        assert columns == ["id", "name"]
        assert count == 1

    def test_list_tables_empty(self):
        assert self.db.list_tables() == []

    def test_list_tables_with_data(self):
        self.db.create_table("t1", ["id"])
        self.db.create_table("t2", ["id"])
        tables = self.db.list_tables()
        assert len(tables) == 2
        assert "t1" in tables
        assert "t2" in tables

    def test_table_exists_false(self):
        assert self.db.table_exists("ghost") is False

    def test_select_records_invalid_filter_key(self):
        self.db.create_table("students", ["id", "name"])
        self.db.insert_record("students", (1, "Иван"))
        records = self.db.select_records("students", ghost="value")
        assert len(records) == 0

    def test_update_records_invalid_column(self):
        self.db.create_table("students", ["id", "name"])
        self.db.insert_record("students", (1, "Иван"))
        with pytest.raises(ColumnNotFoundError):
            self.db.update_records("students", {"ghost": "value"})

    def test_rename_table_success(self):
        self.db.create_table("old", ["id"])
        self.db.rename_table("old", "new")
        assert "new" in self.db.list_tables()
        assert "old" not in self.db.list_tables()

    def test_rename_table_not_found(self):
        with pytest.raises(TableNotFoundError):
            self.db.rename_table("ghost", "new")

    def test_rename_table_empty_name(self):
        self.db.create_table("test", ["id"])
        with pytest.raises(EmptyTableNameError):
            self.db.rename_table("", "new")
        with pytest.raises(EmptyTableNameError):
            self.db.rename_table("test", "")

    def test_rename_column_success(self):
        self.db.create_table("students", ["old_name", "age"])
        self.db.insert_record("students", ("Иван", 20))
        self.db.rename_column("students", "old_name", "new_name")
        columns = self.db.get_columns("students")
        assert "new_name" in columns
        assert "old_name" not in columns
        # Проверяем, что данные сохранились
        records = self.db.select_records("students")
        assert records[0][0] == "Иван"

    def test_rename_column_not_found(self):
        self.db.create_table("students", ["name"])
        with pytest.raises(ColumnNotFoundError):
            self.db.rename_column("students", "ghost", "new")

    def test_rename_column_duplicate(self):
        self.db.create_table("students", ["name", "age"])
        with pytest.raises(ColumnNotFoundError):
            self.db.rename_column("students", "name", "age")

    def test_insert_record_wrong_length(self):
        self.db.create_table("students", ["id", "name"])
        with pytest.raises(InvalidRecordLengthError):
            self.db.insert_record("students", (1,))

    def test_delete_records_no_matches(self):
        self.db.create_table("students", ["id", "name"])
        self.db.insert_record("students", (1, "Иван"))
        deleted = self.db.delete_records("students", name="Ghost")
        assert deleted == 0

    def test_update_records_no_matches(self):
        self.db.create_table("students", ["id", "name"])
        self.db.insert_record("students", (1, "Иван"))
        updated = self.db.update_records("students", {"name": "Анна"}, name="Ghost")
        assert updated == 0

    def test_sort_records_empty(self):
        self.db.create_table("students", ["name"])
        sorted_records = self.db.sort_records("students", "name", reverse=False)
        assert sorted_records == []

    def test_sort_records_column_not_found(self):
        self.db.create_table("students", ["name"])
        with pytest.raises(ColumnNotFoundError):
            self.db.sort_records("students", "ghost")

    def test_delete_table_not_found(self):
        with pytest.raises(TableNotFoundError):
            self.db.delete_table("ghost")

    def test_clear_table_empty(self):
        self.db.create_table("students", ["id"])
        self.db.clear_table("students")  # не должно упасть
        assert len(self.db.select_records("students")) == 0



