from typing import List, Dict, Any, Optional


class DatabaseError(Exception):
    pass


class RecordNotFoundError(DatabaseError):
    pass


class ValidationError(DatabaseError):
    pass


class Table:


    def __init__(self):
        self._data: Dict[int, Dict] = {}
        self._next_id = 1

    def insert(self, record: Dict) -> Dict:

        record["id"] = self._next_id
        self._data[self._next_id] = record.copy()
        self._next_id += 1
        return self._data[self._next_id - 1]

    def get_all(self, filters: Optional[Dict] = None) -> List[Dict]:

        result = list(self._data.values())

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