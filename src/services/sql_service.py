from dataclasses import dataclass

import pandas as pd
from plotly.graph_objects import Figure

from database.execute_query import QueryExecutor
from llm.insight_generator import InsightGenerator
from llm.intent_classifier import IntentClassifier
from llm.sql_generator import SQLGenerator
from services.topic_filter import is_plausibly_domain_related
from services.validation_service import SQLValidator
from services.visualization_service import VisualizationService


class SQLServiceError(Exception):
    """Raised when the SQL service fails."""


OFF_TOPIC_MESSAGE = (
    "I'm focused on ESG manufacturing data — things like emissions, "
    "energy, water, waste, workforce, and compliance metrics across "
    "facilities. Try asking a question about that data, for example: "
    "\"What are the top 5 facilities by Scope 1 emissions?\""
)


@dataclass
class QueryResult:
    question: str
    sql: str
    dataframe: pd.DataFrame
    insight: str
    chart: Figure | None


class SQLService:
    """Coordinates the complete Text-to-SQL pipeline."""

    @classmethod
    def process_question(cls, question: str) -> QueryResult:

        question = question.strip()

        if not question:
            raise SQLServiceError("Question cannot be empty.")

        # Deterministic pre-filter: catches greetings, small talk, and
        # clearly off-topic input before any LLM call. This does not
        # depend on the model's judgment, unlike the intent classifier
        # and SQL generator's UNSUPPORTED_QUERY fallback, both of which
        # were observed to be unreliable on their own for this case.
        if not is_plausibly_domain_related(question):
            raise SQLServiceError(OFF_TOPIC_MESSAGE)

        intent = IntentClassifier.classify(question)

        if intent == "WRITE":
            raise SQLServiceError(
                "This assistant is read-only and can't modify, delete, "
                "or add records. I can help you analyze existing ESG "
                "data instead — for example, ask about emissions, "
                "energy use, or workforce metrics by facility, "
                "country, or year."
            )

        if intent == "OFF_TOPIC":
            raise SQLServiceError(OFF_TOPIC_MESSAGE)

        generated_sql = SQLGenerator.generate(question)

        # SQLValidator.validate returns a safe-to-execute version of the
        # query (unknown tables/columns rejected, multiple statements
        # rejected, and a row limit enforced/tightened). Downstream code
        # executes this returned SQL, not the raw LLM output.
        safe_sql = SQLValidator.validate(generated_sql)

        dataframe = QueryExecutor.execute(safe_sql)

        insight = InsightGenerator.generate(
            question,
            safe_sql,
            dataframe,
        )

        chart = VisualizationService.generate(
            question,
            dataframe,
        )

        return QueryResult(
            question=question,
            sql=safe_sql,
            dataframe=dataframe,
            insight=insight,
            chart=chart.figure,
        )