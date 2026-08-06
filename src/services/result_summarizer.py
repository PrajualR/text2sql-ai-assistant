import pandas as pd


class ResultSummarizer:
    """
    Builds a business-oriented summary of a SQL result.

    The summary is deterministic and intended as context for the LLM.
    """

    @classmethod
    def build(
        cls,
        dataframe: pd.DataFrame,
        sql: str,
    ) -> str:

        if dataframe.empty:
            return "No rows returned."

        sections = []

        sections.append(f"Rows Returned: {len(dataframe)}")

        sections.append("")

        sections.extend(cls._summarize_columns(dataframe))

        sections.append("")

        sections.extend(cls._summarize_metrics(dataframe))

        sections.append("")

        sections.extend(cls._sample_rows(dataframe))

        sections.append("")

        sections.append("Generated SQL")

        sections.append(sql)

        return "\n".join(sections)

    # -----------------------------------------------------

    @staticmethod
    def _summarize_columns(df):

        numeric = df.select_dtypes(include="number").columns.tolist()

        categorical = [c for c in df.columns if c not in numeric]

        lines = []

        if categorical:

            lines.append("Dimensions:")

            lines.append(", ".join(categorical))

        if numeric:

            lines.append("Metrics:")

            lines.append(", ".join(numeric))

        return lines

    # -----------------------------------------------------

    @staticmethod
    def _summarize_metrics(df):

        lines = []

        numeric = df.select_dtypes(include="number")

        if numeric.empty:
            return lines

        for column in numeric.columns:

            series = numeric[column]

            lines.append(f"Metric: {column}")

            lines.append(f"Average: {series.mean():,.2f}")

            lines.append(f"Minimum: {series.min():,.2f}")

            lines.append(f"Maximum: {series.max():,.2f}")

            if len(df.columns) >= 2:

                dimension = df.columns[0]

                try:

                    highest_row = df.loc[series.idxmax()]

                    lowest_row = df.loc[series.idxmin()]

                    lines.append(
                        f"Highest: {highest_row[dimension]} ({series.max():,.2f})"
                    )

                    lines.append(
                        f"Lowest: {lowest_row[dimension]} ({series.min():,.2f})"
                    )

                except Exception:
                    pass

            lines.append("")

        return lines

    # -----------------------------------------------------

    @staticmethod
    def _sample_rows(df):

        lines = []

        lines.append("Sample Data")

        lines.append(df.head(10).to_markdown(index=False))

        return lines
