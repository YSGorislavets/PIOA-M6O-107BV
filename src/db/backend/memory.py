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

