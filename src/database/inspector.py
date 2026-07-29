from database.database import db


class DatabaseInspector:
    """Provides database metadata."""

    @staticmethod
    def get_tables() -> list[str]:

        return db.get_usable_table_names()

    @staticmethod
    def get_schema() -> str:

        return db.get_table_info()

    @staticmethod
    def table_exists(table_name: str) -> bool:

        return table_name in db.get_usable_table_names()
