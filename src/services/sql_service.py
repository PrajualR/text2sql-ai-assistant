from dataclasses import dataclass

import pandas as pd
from plotly.graph_objects import Figure

from database.execute_query import QueryExecutor
from llm.insight_generator import InsightGenerator
from llm.intent_classifier import IntentClassifier
from llm.sql_generator import SQLGenerator
from rag.retriever import Retriever
from services.topic_filter import is_plausibly_domain_related
from services.validation_service import SQLValidator
from services.visualization_service import VisualizationService
from services.conversation import ConversationContext
retriever = Retriever()

class SQLServiceError(Exception):
    """Raised when the SQL service fails."""


OFF_TOPIC_MESSAGE = (
    "I'm focused on ESG manufacturing data — things like emissions, "
    "energy, water, waste, workforce, and compliance metrics across "
    "facilities."
)


@dataclass
class QueryResult:
    question: str
    sql: str
    dataframe: pd.DataFrame
    insight: str
    chart: Figure | None


class SQLService:

    @classmethod
    def process_question(
        cls,
        question: str,
        history: ConversationContext | None = None,
    ) -> QueryResult:

        question = question.strip()

        if not question:
            raise SQLServiceError("Question cannot be empty.")

        history_text = history.combined_text() if history else ""

        if not is_plausibly_domain_related(question, history_text):
            raise SQLServiceError(OFF_TOPIC_MESSAGE)

        intent = IntentClassifier.classify(question)

        if intent == "WRITE":
            raise SQLServiceError(
                "This assistant only supports read-only ESG analytics queries."
            )

        if intent == "OFF_TOPIC" and not history:
            raise SQLServiceError(OFF_TOPIC_MESSAGE)


        retrieved_chunks = retriever.retrieve(
            question
        )

        retrieved_context = retriever.build_context(
            retrieved_chunks
        )

        generated_sql = SQLGenerator.generate(
            question=question,
            retrieved_context=retrieved_context,
            history=history,
        )
        safe_sql = SQLValidator.validate(generated_sql)

        dataframe = QueryExecutor.execute(safe_sql)

        insight = InsightGenerator.generate(question, safe_sql, dataframe)

        chart = VisualizationService.generate(question, dataframe)

        if history is not None:
            history.add(question, safe_sql)

        return QueryResult(
            question=question, sql=safe_sql, dataframe=dataframe,
            insight=insight, chart=chart.figure,
        )