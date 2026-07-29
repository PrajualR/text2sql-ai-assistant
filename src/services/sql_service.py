from dataclasses import dataclass

import pandas as pd
from plotly.graph_objects import Figure

from database.execute_query import QueryExecutor
from llm.insight_generator import InsightGenerator
from llm.intent_classifier import IntentClassifier
from llm.sql_generator import SQLGenerator
from services.validation_service import SQLValidator
from services.visualization_service import VisualizationService


class SQLServiceError(Exception):
    """Raised when the SQL service fails."""


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

        intent = IntentClassifier.classify(question)

        if intent == "WRITE":
            raise SQLServiceError(
                "This assistant supports read-only analytical queries."
            )

        sql = SQLGenerator.generate(question)

        SQLValidator.validate(sql)

        dataframe = QueryExecutor.execute(sql)

        insight = InsightGenerator.generate(
            question,
            sql,
            dataframe,
        )

        chart = VisualizationService.generate(
            question,
            dataframe,
        )

        return QueryResult(
            question=question,
            sql=sql,
            dataframe=dataframe,
            insight=insight,
            chart=chart.figure,
        )
