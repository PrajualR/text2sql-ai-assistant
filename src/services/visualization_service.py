"""
Visualization recommendation service.

Determines the best chart based on:
1. User question
2. SQL result (DataFrame)
"""

from dataclasses import dataclass

import pandas as pd

from visualization.chart_factory import ChartFactory


@dataclass
class ChartRecommendation:
    chart_type: str
    figure: object | None


class VisualizationService:
    """Recommends and creates Plotly visualizations."""

    @classmethod
    def generate(
        cls,
        question: str,
        dataframe: pd.DataFrame,
    ) -> ChartRecommendation:

        if dataframe.empty:
            return ChartRecommendation(
                chart_type="NONE",
                figure=None,
            )

        chart = cls._recommend_chart(
            question,
            dataframe,
        )

        figure = cls._build_chart(
            chart,
            question,
            dataframe,
        )

        return ChartRecommendation(
            chart_type=chart,
            figure=figure,
        )

    @staticmethod
    def _recommend_chart(
        question: str,
        dataframe: pd.DataFrame,
    ) -> str:

        question = question.lower()

        rows = len(dataframe)
        cols = len(dataframe.columns)

        numeric_cols = dataframe.select_dtypes(include="number").columns.tolist()

        categorical_cols = [c for c in dataframe.columns if c not in numeric_cols]

        # -------------------------------
        # KPI
        # -------------------------------

        if rows == 1 and len(numeric_cols) == 1 and cols == 1:
            return "METRIC"

        # -------------------------------
        # Time Series
        # -------------------------------

        time_columns = {
            "Fiscal_Year",
            "Year",
            "Month",
            "Quarter",
            "Date",
        }

        if any(col in time_columns for col in dataframe.columns):
            return "LINE"

        # -------------------------------
        # Correlation
        # -------------------------------

        if len(numeric_cols) >= 2:

            if any(
                word in question
                for word in [
                    "correlation",
                    "relationship",
                    "vs",
                    "versus",
                ]
            ):
                return "SCATTER"

        # -------------------------------
        # Pie Chart
        # -------------------------------

        if len(categorical_cols) == 1 and len(numeric_cols) == 1 and rows <= 8:
            if any(
                word in question
                for word in [
                    "share",
                    "distribution",
                    "percentage",
                    "proportion",
                ]
            ):
                return "PIE"

        # -------------------------------
        # Horizontal Bar
        # -------------------------------

        if any(
            word in question
            for word in [
                "top",
                "highest",
                "lowest",
                "bottom",
            ]
        ):
            return "HBAR"

        # -------------------------------
        # Default Comparison
        # -------------------------------

        if len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
            return "BAR"

        return "NONE"

    @staticmethod
    def _build_chart(
        chart: str,
        question: str,
        df: pd.DataFrame,
    ):

        if chart == "METRIC":

            value = df.iloc[0, 0]

            return ChartFactory.metric(
                value=value,
                title=question,
            )

        numeric = df.select_dtypes(include="number").columns.tolist()

        categorical = [c for c in df.columns if c not in numeric]

        if not numeric:
            return None

        y = numeric[0]

        if categorical:
            x = categorical[0]
        else:
            x = df.index

        if chart == "BAR":

            return ChartFactory.bar(
                df=df,
                x=x,
                y=y,
                title=question,
            )

        if chart == "HBAR":

            return ChartFactory.horizontal_bar(
                df=df,
                x=y,
                y=x,
                title=question,
            )

        if chart == "LINE":

            return ChartFactory.line(
                df=df,
                x=x,
                y=y,
                title=question,
            )

        if chart == "PIE":

            return ChartFactory.pie(
                df=df,
                names=x,
                values=y,
                title=question,
            )

        if chart == "SCATTER":

            if len(numeric) < 2:
                return None

            return ChartFactory.scatter(
                df=df,
                x=numeric[0],
                y=numeric[1],
                title=question,
            )

        return None
