import pytest
from src.db.backend.memory import Table
from src.db.backend.errors import RecordNotFoundError, ValidationError


class TestTable:

    def setup_method(self):
        self.table = Table()

    def test_insert(self):
        record = self.table.insert({
            "name": "Иван Петров",
            "group": "М-101"
        })
        assert record["id"] == 1
        assert record["name"] == "Иван Петров"
        assert record["group"] == "М-101"

    def test_insert_multiple(self):
        self.table.insert({"name": "Первый"})
        self.table.insert({"name": "Второй"})
        assert self.table.count() == 2

    def test_get_all_empty(self):
        assert self.table.get_all() == []

    def test_get_all_with_data(self):
        self.table.insert({"name": "Студент 1"})
        self.table.insert({"name": "Студент 2"})
        records = self.table.get_all()
        assert len(records) == 2

    def test_get_all_with_filter(self):
        self.table.insert({"name": "Анна", "group": "М-101"})
        self.table.insert({"name": "Иван", "group": "М-102"})
        self.table.insert({"name": "Мария", "group": "М-101"})

        # Фильтр по группе
        filtered = self.table.get_all({"group": "М-101"})
        assert len(filtered) == 2
        assert all(r["group"] == "М-101" for r in filtered)

    def test_get_all_with_multiple_filters(self):
        self.table.insert({"name": "Анна", "group": "М-101", "grade": 5})
        self.table.insert({"name": "Анна", "group": "М-102", "grade": 4})
        self.table.insert({"name": "Иван", "group": "М-101", "grade": 5})


        filtered = self.table.get_all({"name": "Анна", "group": "М-101"})
        assert len(filtered) == 1
        assert filtered[0]["grade"] == 5

    def test_get_by_id_success(self):
        self.table.insert({"name": "Тест"})
        record = self.table.get_by_id(1)
        assert record["name"] == "Тест"
        assert record["id"] == 1

    def test_get_by_id_not_found(self):
        with pytest.raises(RecordNotFoundError):
            self.table.get_by_id(999)

    def test_update_success(self):
        self.table.insert({"name": "Старое имя", "group": "М-101"})
        updated = self.table.update(1, {"name": "Новое имя"})
        assert updated["name"] == "Новое имя"
        assert updated["group"] == "М-101"

    def test_update_not_found(self):
        with pytest.raises(RecordNotFoundError):
            self.table.update(999, {"name": "test"})

    def test_delete_success(self):
        self.table.insert({"name": "Удалить меня"})
        assert self.table.delete(1) is True
        assert self.table.count() == 0

    def test_delete_not_found(self):
        with pytest.raises(RecordNotFoundError):
            self.table.delete(999)

    def test_count(self):

        assert self.table.count() == 0
        self.table.insert({"name": "1"})
        assert self.table.count() == 1
        self.table.insert({"name": "2"})
        assert self.table.count() == 2

    def test_get_all_sorted_ascending(self):

        self.table.insert({"name": "Иван", "grade": 3})
        self.table.insert({"name": "Анна", "grade": 5})
        self.table.insert({"name": "Борис", "grade": 4})

        sorted_records = self.table.get_all(sort_by="name", reverse=False)
        names = [r["name"] for r in sorted_records]
        assert names == ["Анна", "Борис", "Иван"]

    def test_get_all_sorted_descending(self):

        self.table.insert({"name": "Иван", "grade": 3})
        self.table.insert({"name": "Анна", "grade": 5})
        self.table.insert({"name": "Борис", "grade": 4})

        sorted_records = self.table.get_all(sort_by="grade", reverse=True)
        grades = [r["grade"] for r in sorted_records]
        assert grades == [5, 4, 3]

    def test_get_all_with_filter_and_sort(self):

        self.table.insert({"name": "Анна", "group": "М-101", "grade": 5})
        self.table.insert({"name": "Борис", "group": "М-102", "grade": 4})
        self.table.insert({"name": "Вера", "group": "М-101", "grade": 3})

        result = self.table.get_all(
            filters={"group": "М-101"},
            sort_by="grade",
            reverse=False
        )
        grades = [r["grade"] for r in result]
        assert grades == [3, 5]

