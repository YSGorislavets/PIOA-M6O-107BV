class DatabaseError(Exception):
    pass

class RecordNotFoundError(DatabaseError):
    pass

class ValidationError(DatabaseError):
    pass

class DuplicateError(DatabaseError):
    pass
class TableError(Exception):
    """Базовый класс для ошибок таблицы"""
    pass


class TableNotFoundError(TableError):
    """Ошибка: таблица не найдена"""
    pass


class ColumnNotFoundError(TableError):
    """Ошибка: колонка не найдена"""
    pass


class DuplicateTableError(TableError):
    """Ошибка: таблица с таким именем уже существует"""
    pass


class EmptyTableNameError(TableError):
    """Ошибка: имя таблицы не может быть пустым"""
    pass


class EmptyColumnsError(TableError):
    """Ошибка: таблица должна содержать хотя бы одну колонку"""
    pass


class InvalidRecordLengthError(TableError):
    """Ошибка: длина записи не соответствует количеству колонок"""
    pass


class RecordNotFoundError(TableError):
    """Ошибка: запись с указанным индексом не найдена"""
    pass


class InvalidColumnNameError(TableError):
    """Ошибка: недопустимое название колонки (повторяющиеся имена)"""
    pass


class FileOperationError(TableError):
    """Ошибка: проблема с файловой операцией (чтение/запись/удаление)"""
    pass


class InvalidFileFormatError(TableError):
    """Ошибка: некорректный формат файла данных (не JSON/невалидный JSON)"""
    pass


class ValidationError(TableError):
    """Ошибка: неверные данные (оценка не 0-5, пустые поля и т.д.)"""
    pass

