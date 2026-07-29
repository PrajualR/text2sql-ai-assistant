from langchain_core.output_parsers import StrOutputParser

from database.inspector import DatabaseInspector
from llm.client import llm
from llm.prompts import SQL_GENERATION_PROMPT


class SQLGenerationError(Exception):
    """Raised when SQL generation fails."""


class SQLGenerator:
    """Generates SQLite SELECT statements."""

    @classmethod
    def generate(cls, question: str) -> str:
        """
        Generate SQL from a natural language question.

        Args:
            question: User's natural language question.

        Returns:
            Generated SQL query.

        Raises:
            SQLGenerationError
        """

        schema = DatabaseInspector.get_schema()

        chain = SQL_GENERATION_PROMPT | llm | StrOutputParser()

        try:
            sql = chain.invoke({"schema": schema, "question": question}).strip()

        except Exception as exc:
            raise SQLGenerationError(f"SQL generation failed: {exc}") from exc

        if not sql:
            raise SQLGenerationError("LLM returned an empty SQL query.")

        if sql.upper() == "UNSUPPORTED_QUERY":
            raise SQLGenerationError(
                "The requested information is not available in the current database schema."
            )

        return sql
