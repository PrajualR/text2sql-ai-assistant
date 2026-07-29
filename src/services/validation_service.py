from sqlglot import parse_one
from sqlglot.errors import ParseError
from sqlglot.expressions import Column, Select, Table

from database.inspector import DatabaseInspector


class SQLValidationError(Exception):
    """Raised when SQL validation fails."""


class SQLValidator:

    @classmethod
    def validate(cls, sql: str) -> None:

        try:
            tree = parse_one(sql, read="sqlite")

        except ParseError as exc:
            raise SQLValidationError(f"Invalid SQL: {exc}") from exc


        if not isinstance(tree, Select):
            raise SQLValidationError("Only SELECT statements are allowed.")


        valid_tables = set(DatabaseInspector.get_tables())

        referenced_tables = {table.name for table in tree.find_all(Table)}

        for table in referenced_tables:

            if table not in valid_tables:

                raise SQLValidationError(f"Unknown table: {table}")

        valid_columns = cls._get_all_columns()

        referenced_columns = {column.name for column in tree.find_all(Column)}

        for column in referenced_columns:

            if column not in valid_columns:

                raise SQLValidationError(f"Unknown column: {column}")

    @staticmethod
    def _get_all_columns() -> set[str]:
        """
        Extract all column names from the schema.
        """

        schema = DatabaseInspector.get_schema()

        columns = set()

        capture = False

        for line in schema.splitlines():

            line = line.strip()

            if line.startswith("CREATE TABLE"):
                capture = True
                continue

            if capture:

                if line.startswith(")"):
                    capture = False
                    continue

                if not line:
                    continue

                column = line.split()[0].strip('"').strip(",")

                columns.add(column)

        return columns
