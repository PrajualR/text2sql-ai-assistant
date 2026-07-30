import logging

import streamlit as st

from database.execute_query import QueryExecutionError
from llm.intent_classifier import IntentClassificationError
from llm.sql_generator import SQLGenerationError
from services.sql_service import SQLService, SQLServiceError
from services.validation_service import SQLValidationError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)

def handle_query_error(exc: Exception) -> str:

    if isinstance(exc, SQLServiceError):
        # Currently raised for empty questions and WRITE-intent
        # questions. The message from SQLService is already
        # user-appropriate, so surface it directly.
        logger.warning("Blocked request: %s", exc)
        return str(exc)

    if isinstance(exc, IntentClassificationError):
        logger.error("Intent classification failed: %s", exc)
        return (
            "I couldn't determine how to handle that question. "
            "Try rephrasing it as a direct question about the ESG data."
        )

    if isinstance(exc, SQLGenerationError):
        logger.error("SQL generation failed: %s", exc)
        return (
            "I couldn't translate that question into a query against "
            "the available data. Try rephrasing it, or ask about a "
            "specific metric, facility, country, or year."
        )

    if isinstance(exc, SQLValidationError):
        logger.error("SQL validation failed: %s", exc)
        return (
            "The generated query referenced data outside what's "
            "available. Try rephrasing your question using terms "
            "closer to the dataset (e.g. facility, country, industry, "
            "fiscal year, emissions, energy, waste, workforce)."
        )

    if isinstance(exc, QueryExecutionError):
        logger.error("Query execution failed: %s", exc)
        return (
            "Something went wrong while running that query against the "
            "database. Please try again, and let us know if it keeps "
            "happening."
        )

    # Anything unexpected: log the full detail, show a generic message.
    logger.exception("Unexpected error while processing question.")
    return (
        "Something unexpected went wrong while processing your "
        "question. Please try again."
    )

st.set_page_config(
    page_title="ESG Analytics Assistant",
    page_icon="📊",
    layout="wide",
)

st.title("ESG Natural Language Analytics Assistant")

st.caption(
    "Ask ESG-related questions in plain English and receive insights, visualizations, and query results."
)


if "result" not in st.session_state:
    st.session_state.result = None


question = st.text_area(
    "Ask your question",
    placeholder="Example: Compare Scope 1 emissions by country",
    height=120,
)


if st.button("Generate Insights", use_container_width=True):

    if not question.strip():
        st.warning("Please enter a question.")
        st.stop()

    with st.spinner("Analyzing ESG data..."):

        try:

            st.session_state.result = SQLService.process_question(question)

        except Exception as e:

            st.session_state.result = None
            st.error(handle_query_error(e))


if st.session_state.result is not None:

    result = st.session_state.result

    st.subheader("💡 AI Insight")

    st.success(result.insight)

    if result.chart:

        st.subheader("📈 Visualization")

        st.plotly_chart(
            result.chart,
            use_container_width=True,
        )

    st.subheader("📋 Query Results")

    if result.dataframe.empty:

        st.info("No records found.")

    else:

        st.dataframe(
            result.dataframe,
            use_container_width=True,
            hide_index=True,
        )

        csv = result.dataframe.to_csv(index=False).encode("utf-8")

        st.download_button(
            "⬇ Download CSV",
            data=csv,
            file_name="query_results.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with st.expander("Generated SQL"):

        st.code(
            result.sql,
            language="sql",
        )