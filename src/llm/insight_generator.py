import pandas as pd
from langchain_core.output_parsers import StrOutputParser

from llm.client import llm
from llm.prompts import INSIGHT_PROMPT
from services.result_summarizer import ResultSummarizer


class InsightGenerator:

    @classmethod
    def generate(
        cls,
        question: str,
        sql: str,
        dataframe: pd.DataFrame,
    ) -> str:

        if dataframe.empty:
            return "No records were returned for the requested query."

        summary = ResultSummarizer.build(
            dataframe=dataframe,
            sql=sql,
        )

        chain = INSIGHT_PROMPT | llm | StrOutputParser()

        return chain.invoke(
            {
                "question": question,
                "summary": summary,
            }
        )
