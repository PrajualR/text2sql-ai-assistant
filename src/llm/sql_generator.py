from langchain_core.output_parsers import StrOutputParser

from database.inspector import DatabaseInspector
from llm.client import llm
from llm.prompts import SQL_GENERATION_PROMPT
from services.conversation import ConversationContext


class SQLGenerationError(Exception):
    """Raised when SQL generation fails."""


class SQLGenerator:

    @classmethod
    def generate(cls, question: str, history: ConversationContext | None = None) -> str:

        schema = DatabaseInspector.get_schema()
        history_text = history.as_prompt_text() if history else "No prior conversation in this session."

        chain = SQL_GENERATION_PROMPT | llm | StrOutputParser()

        try:
            sql = chain.invoke(
                {"schema": schema, "question": question, "history": history_text}
            ).strip()

        except Exception as exc:
            raise SQLGenerationError(f"SQL generation failed: {exc}") from exc

        if not sql:
            raise SQLGenerationError("LLM returned an empty SQL query.")

        if sql.upper() == "UNSUPPORTED_QUERY":
            raise SQLGenerationError(
                "The requested information is not available in the current database schema."
            )

        return sql