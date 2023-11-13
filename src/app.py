import logging
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from config import settings

logger = logging.getLogger("solar_app")

st.set_page_config(
    page_title="Energy Production",
    page_icon=":chart_with_upwards_trend:",
    layout="wide",
)


@st.cache_data
def load_csv(filepath, frequency):
    logger.info("Carregando dados de produção de energia")

    df = pd.read_csv(filepath, parse_dates=["date_time"])
    df.set_index("date_time", inplace=True)
    df = df.sort_index()
    df = df.asfreq(frequency)
    return df


def aggregate_ldtea(df):
    logger.info("Iniciando aggregate_ldtea")

    df_agg = pd.DataFrame()
    df_agg["ldtea"] = df[["LDTEA 1", "LDTEA 2", "LDTEA 3", "LDTEA 4"]].mean(axis=1)
    return df_agg


def add_time_features(df):
    logger.info("Adicionando recursos temporais - Time Features")

    df = df.copy()
    df["hour"] = df.index.hour
    df["day"] = df.index.day
    df["weekday"] = df.index.weekday
    df["month"] = df.index.month
    df["weekend"] = df.weekday.isin([5, 6]).astype(int)
    df["is_night"] = ((df["hour"] >= 18) | (df["hour"] <= 6)).astype(int)
    df["month_name"] = df["month"].map(settings.MONTH_MAPPING)
    df["day_name"] = df["weekday"].map(settings.DAY_MAPPING)
    return df


def run_app():
    logger.info("Iniciando run_app")

    freq = settings.FREQUENCY
    file_path = Path(settings.FILEPATH)

    if not file_path.exists():
        logger.error("Arquivo %s não encontrado", file_path)
        st.error(f"Arquivo {file_path} não encontrado")
        return

    df_raw = load_csv(file_path, freq)
    df_agg = aggregate_ldtea(df_raw)
    df = add_time_features(df_agg)
    df.sort_index(inplace=True)

    st.title("Energy Production")
    st.write(df_raw.head())
    st.write(df_agg.head())
    st.write(df.head())

    st.subheader("Energy Production by Month")
    st.bar_chart(df.groupby("month_name").mean()["ldtea"])

    st.line_chart(df[["ldtea"]])

    with st.expander("Energy Production by Day"):
        st.dataframe(df)
