import pandas as pd
from langchain_core.output_parsers import StrOutputParser

from llm.client import llm
from llm.prompts import INSIGHT_PROMPT


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

        summary = cls._build_summary(
            sql,
            dataframe,
        )

        chain = INSIGHT_PROMPT | llm | StrOutputParser()

        return chain.invoke(
            {
                "question": question,
                "summary": summary,
            }
        )

    @staticmethod
    def _build_summary(
        sql: str,
        dataframe: pd.DataFrame,
    ) -> str:

        info = []

        info.append(f"Rows Returned: {len(dataframe)}")

        info.append(f"Columns: {', '.join(dataframe.columns)}")

        info.append("")

        info.append("Generated SQL:")

        info.append(sql)

        info.append("")

        numeric = dataframe.select_dtypes(include="number")

        if not numeric.empty:

            info.append("Numeric Summary")

            info.append(numeric.describe().to_markdown())

            info.append("")

        info.append("Sample Data")

        info.append(dataframe.head(10).to_markdown(index=False))

        return "\n".join(info)
