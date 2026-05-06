from copy import deepcopy
from typing import List, Dict, Any, Optional
from src.db.backend.errors import DatabaseError, RecordNotFoundError, ValidationError, DuplicateError


class Table:
    def __init__(self):
        self._data: Dict[int, Dict] = {}
        self._next_id = 1

    def insert(self, record: Dict) -> Dict:
        record["id"] = self._next_id
        self._data[self._next_id] = record.copy()
        self._next_id += 1
        return self._data[self._next_id - 1].copy()

    def get_all(self, filters: Optional[Dict] = None) -> List[Dict]:
        # Возвращаем глубокие копии записей, чтобы внешний код не мог изменить БД
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
            return filtered
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
