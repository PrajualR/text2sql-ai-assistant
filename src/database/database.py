from pathlib import Path

from langchain_community.utilities import SQLDatabase
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


class DatabaseManager:
    """
    Responsible for creating and managing the SQLite connection.
    """

    def __init__(self) -> None:

        self.project_root = Path(__file__).resolve().parents[2]

        self.database_path = self.project_root / "data" / "esg.db"

        if not self.database_path.exists():
            raise FileNotFoundError(f"Database not found:\n{self.database_path}")

        self.database_url = f"sqlite:///{self.database_path}"

        self.engine = create_engine(self.database_url, future=True)

        self.database = SQLDatabase(engine=self.engine)

    @property
    def sql_engine(self) -> Engine:
        return self.engine

    @property
    def sql_database(self) -> SQLDatabase:
        return self.database


_database_manager = DatabaseManager()

engine = _database_manager.sql_engine

db = _database_manager.sql_database
