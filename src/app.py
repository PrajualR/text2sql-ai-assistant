import streamlit as st

from services.sql_service import SQLService

st.set_page_config(
    page_title="ESG Analytics Assistant",
    page_icon="📊",
    layout="wide",
)

st.title("📊 ESG Natural Language Analytics Assistant")

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
            st.error(str(e))


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
