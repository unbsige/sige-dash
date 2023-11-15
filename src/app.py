import logging
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image

from config import settings
from plot_utils import plot_go_scatter, plot_graph_bar, plot_graph_line

logger = logging.getLogger("solar_app")

st.set_page_config(
    page_title="Produção de Energia",
    page_icon=":chart_with_upwards_trend:",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource
def load_dataset(filepath, frequency):
    logger.info("Carregando dados de produção de energia")

    df = pd.read_csv(filepath, parse_dates=["date_time"])
    df.set_index("date_time", inplace=True)
    df = df.sort_index()
    df = df.asfreq(frequency)
    return df


def load_add_cache(file_path, freq):
    df_raw = load_dataset(file_path, freq)
    df_agg = aggregate_ldtea(df_raw)
    df = add_time_features(df_agg)
    df.sort_index(inplace=True)
    st.session_state["df"] = df
    st.session_state["df_raw"] = df_raw
    st.session_state["df_agg"] = df_agg


def aggregate_ldtea(df):
    logger.info("Iniciando aggregate_ldtea")

    df_agg = df.copy()
    df_agg["avg_ldtea"] = df[["LDTEA 1", "LDTEA 2", "LDTEA 3", "LDTEA 4"]].mean(axis=1)
    df_agg["avg_uac"] = df_agg[["UAC 2", "UAC 3"]].mean(axis=1)
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

    st.title("Produção de energia solar UnB ⚡")
    st.subheader("Dataframes")

    df = st.session_state["df"]
    df_raw = st.session_state["df_raw"]
    df_agg = st.session_state["df_agg"]

    col1, col2 = st.columns(2)
    with col1.expander("Produção de energia - dados brutos"):
        st.dataframe(df_raw)

    with col2.expander("Produção de energia - agregando os predios"):
        st.dataframe(df_agg)

    df_day = df.groupby("day").mean()["avg_ldtea"]
    with col1.expander("Produção media de energia por dia"):
        st.dataframe(df_day)

    df_month_avg = df.groupby("month_name").sum()["avg_ldtea"]
    with col2.expander("Produção media de energia por mes"):
        st.dataframe(df_month_avg)

    with st.expander("Produção de energia - dataset completo"):
        st.dataframe(df)

    # =================================================================================================================
    st.write(" ")
    st.divider()
    st.subheader("Graficos")
    st.sidebar.subheader("Filtros")

    cols = df_agg.columns
    c1, _, c3, _ = st.columns([5, 2, 20, 2])
    months = df["month_name"].unique()
    months = np.insert(months, 0, "todos")

    month = c1.selectbox(
        "Selecione o mês",
        months,
        key="month",
        help="Selecione o mês para visualizar os gráficos",
    )
    y_columns = c1.multiselect(
        "Selecione os medidores",
        cols,
        key="y_columns",
        default=["LDTEA 1"],
        help="Selecione os medidores para visualizar os gráficos",
    )

    df_month = df[df["month_name"] == month] if month != "todos" else df
    with c3.container():
        init_date, end_date = st.slider(
            "Selecione o intervalo:",
            min_value=df_month.index.min().date(),
            max_value=df_month.index.max().date(),
            value=(df_month.index.min().date(), df_month.index.max().date()),
            step=None,
            format="DD/MM/YYYY",
            help="Selecione o intervalo para visualizar os gráficos",
        )
    df_month = df_month.loc[init_date:end_date]
    plot_graph_line(
        df_month,
        df_month.index,
        y_columns,
        "Produção de Energia",
    )

    st.write(" ")
    st.divider()

    y_column = st.sidebar.selectbox(
        "Selecione o medidor",
        cols,
        help="Selecione o medidor para visualizar os gráficos",
    )

    c1, c2, *_ = st.columns(4)
    start_date = c1.date_input("Data inicial", value=df.index.min())
    end_date = c2.date_input("Data final", value=df.index.max())

    df_date = df.loc[start_date:end_date]
    plot_graph_line(
        df_date,
        df_date.index,
        y_column,
        f"{y_column} - Produção de Energia: ({start_date} - {end_date})",
    )

    st.write(" ")
    st.markdown("---")

    df_day = df.groupby("day").mean()[y_column]
    df_day = df_day.round(2)
    plot_graph_bar(
        df_day, df_day.index, y_column, f"Produção media de energia por dia do mês({y_column})"
    )

    c1, c2 = st.columns(2)
    with c1:
        df_month = df.groupby("month").agg({y_column: "sum", "month_name": "first"})
        plot_graph_bar(
            df_month,
            df_month["month_name"],
            y_column,
            f"Produção total de energia por mês: {y_column}",
        )

    with c2:
        df_week = df.groupby("weekday").agg({y_column: "mean", "day_name": "first"})
        df_week = df_week.round(2)
        plot_graph_bar(
            df_week,
            df_week["day_name"],
            y_column,
            f"Produção media de energia por dia da semana: {y_column}",
        )

    st.write(" ")
    st.markdown("---")

    plot_go_scatter(df, "date_time", y_column, f"Produção de Energia {y_column}")


def main():
    logger.info("Iniciando main")
    logo = Image.open(settings.ROOT_DIR / "assets" / "unb_logo.jpeg")

    st.sidebar.title("UnB - Solar Production")
    st.sidebar.image(logo, use_column_width=True)

    freq = settings.FREQUENCY
    file_path = Path(settings.FILEPATH)

    if not file_path.exists():
        logger.error("Arquivo %s não encontrado", file_path)
        st.error(f"Arquivo {file_path} não encontrado")
        return

    if "data" not in st.session_state:
        load_add_cache(file_path, freq)

    run_app()
