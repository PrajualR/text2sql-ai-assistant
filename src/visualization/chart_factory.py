from typing import Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


class ChartFactory:
    """Creates Plotly charts."""

    @staticmethod
    def bar(df: pd.DataFrame, x: str, y: str, title: str):

        return px.bar(
            df,
            x=x,
            y=y,
            title=title,
            text_auto=True,
        )

    @staticmethod
    def horizontal_bar(df: pd.DataFrame, x: str, y: str, title: str):

        return px.bar(
            df,
            x=x,
            y=y,
            orientation="h",
            title=title,
            text_auto=True,
        )

    @staticmethod
    def line(df: pd.DataFrame, x: str, y: str, title: str):

        return px.line(
            df,
            x=x,
            y=y,
            title=title,
            markers=True,
        )

    @staticmethod
    def pie(df: pd.DataFrame, names: str, values: str, title: str):

        return px.pie(
            df,
            names=names,
            values=values,
            title=title,
        )

    @staticmethod
    def scatter(
        df: pd.DataFrame,
        x: str,
        y: str,
        title: str,
        color: Optional[str] = None,
    ):

        return px.scatter(
            df,
            x=x,
            y=y,
            color=color,
            title=title,
        )

    @staticmethod
    def metric(value, title: str):

        fig = go.Figure(
            go.Indicator(
                mode="number",
                value=value,
                title={"text": title},
            )
        )

        return fig
