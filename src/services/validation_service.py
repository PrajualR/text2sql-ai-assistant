import sqlglot
from sqlalchemy import inspect
from sqlglot import exp
from sqlglot.errors import ParseError
from sqlglot.expressions import Column, Select, Table

from database.database import engine
from database.inspector import DatabaseInspector

# Hard cap on rows returned by any query. Applied server-side by injecting
# or tightening a LIMIT clause on the parsed AST, so an overly broad
# question can never pull back the entire table.
MAX_ROWS = 1000


class SQLValidationError(Exception):
    """Raised when SQL validation fails."""


class SQLValidator:

    @classmethod
    def validate(cls, sql: str) -> str:
        """
        Validate a generated SQL string and return a safe-to-execute
        version of it (with a row limit enforced).

        Raises:
            SQLValidationError: if the SQL is invalid, unsafe, or
                references unknown tables/columns.
        """

        cls._reject_multiple_statements(sql)

        try:
            tree = sqlglot.parse_one(sql, read="sqlite")

        except ParseError as exc:
            raise SQLValidationError(f"Invalid SQL: {exc}") from exc

        if not isinstance(tree, Select):
            raise SQLValidationError("Only SELECT statements are allowed.")

        cls._validate_tables(tree)
        cls._validate_columns(tree)

        safe_tree = cls._enforce_row_limit(tree)

        return safe_tree.sql(dialect="sqlite")

    @staticmethod
    def _reject_multiple_statements(sql: str) -> None:
        """
        Ensure the input contains exactly one SQL statement.

        `parse_one` silently parses only the first statement, so a
        payload like "SELECT 1; DROP TABLE facilities;" would otherwise
        pass validation while smuggling a second statement past it.
        """

        try:
            statements = [s for s in sqlglot.parse(sql, read="sqlite") if s is not None]

        except ParseError as exc:
            raise SQLValidationError(f"Invalid SQL: {exc}") from exc

        if len(statements) == 0:
            raise SQLValidationError("No SQL statement found.")

        if len(statements) > 1:
            raise SQLValidationError(
                "Only a single SELECT statement is allowed per query."
            )

    @staticmethod
    def _validate_tables(tree: Select) -> None:

        valid_tables = set(DatabaseInspector.get_tables())

        referenced_tables = {table.name for table in tree.find_all(Table)}

        for table in referenced_tables:

            if table not in valid_tables:

                raise SQLValidationError(f"Unknown table: {table}")

    @classmethod
    def _validate_columns(cls, tree: Select) -> None:

        valid_columns = cls._get_all_columns()

        # Aliases defined in the SELECT list (e.g. `MAX(x) AS total_x`)
        # are legitimate to reference elsewhere in the query — most
        # commonly in ORDER BY — even though they are not real schema
        # columns. sqlglot parses `ORDER BY total_x` as a genuine
        # Column node, so without this exclusion a perfectly valid
        # query gets rejected as referencing an "unknown column".
        select_aliases = {
            alias.alias
            for alias in tree.selects
            if isinstance(alias, exp.Alias) and alias.alias
        }

        referenced_columns = {
            column.name
            for column in tree.find_all(Column)
            if column.name not in select_aliases
        }

        for column in referenced_columns:

            if column not in valid_columns:

                raise SQLValidationError(f"Unknown column: {column}")

    @staticmethod
    def _get_all_columns() -> set[str]:
        """
        Extract all known column names directly from the live database
        schema via SQLAlchemy's inspector, rather than string-parsing
        `CREATE TABLE` DDL text. This is correct regardless of quoting,
        formatting, or column names that collide with SQL keywords.
        """

        inspector = inspect(engine)

        columns: set[str] = set()

        for table_name in inspector.get_table_names():

            for column_info in inspector.get_columns(table_name):
                columns.add(column_info["name"])

        return columns

    @classmethod
    def _enforce_row_limit(cls, tree: Select) -> Select:
        """
        Guarantee the query cannot return more than MAX_ROWS rows.

        If the query has no LIMIT, one is added. If it has a LIMIT
        higher than MAX_ROWS, it's tightened down to MAX_ROWS. A LIMIT
        already at or below MAX_ROWS is left untouched.
        """

        existing_limit = tree.args.get("limit")

        if existing_limit is None:
            return tree.limit(MAX_ROWS)

        try:
            limit_value = int(existing_limit.expression.this)

        except (AttributeError, TypeError, ValueError):
            # Non-literal or unexpected LIMIT expression: play it safe
            # and clamp to MAX_ROWS rather than trusting it blindly.
            return tree.limit(MAX_ROWS)

        if limit_value > MAX_ROWS:
            return tree.limit(MAX_ROWS)

        return tree
