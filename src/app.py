import logging

import streamlit as st

from database.execute_query import QueryExecutionError
from llm.intent_classifier import IntentClassificationError
from llm.sql_generator import SQLGenerationError
from services.conversation import ConversationContext
from services.sql_service import SQLService, SQLServiceError
from services.validation_service import SQLValidationError

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


def handle_query_error(exc: Exception) -> str:
    if isinstance(exc, SQLServiceError):
        return str(exc)
    if isinstance(exc, IntentClassificationError):
        return "I couldn't determine how to handle that question. Try rephrasing it as a direct question about the ESG data."
    if isinstance(exc, SQLGenerationError):
        return "I couldn't translate that into a query. Try naming a specific metric, facility, country, or year."
    if isinstance(exc, SQLValidationError):
        return "That query referenced data outside what's available. Try terms closer to the dataset (facility, country, industry, fiscal year, emissions, energy, waste, workforce)."
    if isinstance(exc, QueryExecutionError):
        return "Something went wrong running that query. Please try again."
    logger.exception("Unexpected error while processing question.")
    return "Something unexpected went wrong. Please try again."


st.set_page_config(page_title="ESG Analytics Assistant", page_icon="📊", layout="wide")

if "messages" not in st.session_state:
    st.session_state.messages = []  # chat transcript
if "history" not in st.session_state:
    st.session_state.history = ConversationContext()

with st.sidebar:
    st.header("📊 ESG Analytics Assistant")
    st.caption(
        "Ask in plain English. Follow-ups like *“now break that down by facility”* build on your last question."
    )
    if st.button("🔄 New conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.history.clear()
        st.rerun()

    st.divider()
    st.caption("Try asking:")
    examples = [
        "Compare Scope 1 emissions by country",
        "Top 5 facilities by water withdrawal",
        "Trend of waste recycling over the last 3 years",
        "Show women representation by country",
    ]
    for ex in examples:
        if st.button(ex, use_container_width=True, key=f"ex_{ex}"):
            st.session_state.pending_question = ex

st.title("ESG Natural Language Analytics")

# --- replay transcript ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        result = msg.get("result")
        if result:
            if result.chart:
                st.plotly_chart(result.chart, use_container_width=True)
            if not result.dataframe.empty:
                with st.expander("📋 Data & SQL", expanded=False):
                    st.dataframe(
                        result.dataframe, use_container_width=True, hide_index=True
                    )
                    st.code(result.sql, language="sql")
                    csv = result.dataframe.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        "⬇ Download CSV",
                        data=csv,
                        file_name="query_results.csv",
                        mime="text/csv",
                        key=f"dl_{id(result)}",
                    )

# --- input (chat box or a clicked example) ---
question = st.chat_input(
    "Ask about emissions, energy, water, waste, workforce, or compliance..."
)
if "pending_question" in st.session_state:
    question = st.session_state.pop("pending_question")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing..."):
            try:
                result = SQLService.process_question(question, st.session_state.history)
                st.markdown(result.insight)
                if result.chart:
                    st.plotly_chart(result.chart, use_container_width=True)
                if not result.dataframe.empty:
                    with st.expander("📋 Data & SQL", expanded=False):
                        st.dataframe(
                            result.dataframe, use_container_width=True, hide_index=True
                        )
                        st.code(result.sql, language="sql")
                st.session_state.messages.append(
                    {"role": "assistant", "content": result.insight, "result": result}
                )
            except Exception as e:
                error_text = handle_query_error(e)
                st.error(error_text)
                st.session_state.messages.append(
                    {"role": "assistant", "content": error_text, "result": None}
                )
