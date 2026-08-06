import logging

import pandas as pd
from sqlalchemy.exc import SQLAlchemyError

from database.database import engine

logger = logging.getLogger(__name__)

MAX_ROWS = 1000


class QueryExecutionError(Exception):
    """Raised when SQL execution fails."""


class QueryExecutor:
    """Executes validated SQL queries."""

    @staticmethod
    def execute(sql: str) -> pd.DataFrame:
        """
        Execute a SQL SELECT query.

        Args:
            sql: Validated SQL query.

        Returns:
            Pandas DataFrame containing the query result, capped at
            MAX_ROWS rows.

        Raises:
            QueryExecutionError: If query execution fails.
        """

        try:
            logger.info("Executing SQL:\n%s", sql)

            dataframe = pd.read_sql(sql, engine)

            if len(dataframe) > MAX_ROWS:
                logger.warning(
                    "Query returned %d rows, truncating to %d.",
                    len(dataframe),
                    MAX_ROWS,
                )
                dataframe = dataframe.head(MAX_ROWS)

            logger.info(
                "Query executed successfully. Rows returned: %d", len(dataframe)
            )

            return dataframe

        except SQLAlchemyError as exc:
            logger.exception("Database execution failed.")
            raise QueryExecutionError(str(exc)) from exc

        except Exception as exc:
            logger.exception("Unexpected execution error.")
            raise QueryExecutionError(str(exc)) from exc
