import logging

import numpy as np
import streamlit as st
from PIL import Image

from config import settings
from load_data import load_data

# from feature_utils import create_features
from plot_utils import plot_go_scatter, plot_graph_bar, plot_graph_line

logger = logging.getLogger("solar_app")

st.set_page_config(
    page_title="Produção de Energia",
    page_icon=":chart_with_upwards_trend:",
    layout="wide",
    initial_sidebar_state="expanded",
)


def dashboard():
    logger.info("Iniciando Dashboard")

    st.title("Produção de energia solar UnB ⚡")
    st.subheader("Conjunto de dados")

    df_prod = st.session_state.df_prod
    df_rad = st.session_state.df_rad
    df_wth = st.session_state.df_wth

    with st.expander("Conjunto de dados de Produção de energia"):
        st.dataframe(df_prod[settings.TARGETS], use_container_width=True)

    with st.expander("Conjunto de dados Irradiação solar"):
        st.dataframe(df_rad, use_container_width=True)

    with st.expander("Conjunto de dados Meteorológicos"):
        st.dataframe(df_wth, use_container_width=True)

    # =================================================================================================================
    st.write(" ")
    st.divider()
    st.subheader("Gráficos")
    st.sidebar.subheader("Filtros")

    cols = settings.TARGET_AGG + settings.TARGETS

    c1, _, c3, _ = st.columns([5, 2, 20, 2])
    months = df_prod["month_name"].unique()
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
        default=["uac_avg", "ldtea_avg"],
        help="Selecione os medidores para visualizar os gráficos",
    )

    df_month = df_prod[df_prod["month_name"] == month] if month != "todos" else df_prod
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
    start_date = c1.date_input("Data inicial", value=df_prod.index.min())
    end_date = c2.date_input("Data final", value=df_prod.index.max())

    df_date = df_prod.loc[start_date:end_date]
    plot_graph_line(
        df_date,
        df_date.index,
        y_column,
        f"{y_column} - Produção de Energia: ({start_date} - {end_date})",
    )

    st.write(" ")
    st.markdown("---")

    df_day = df_prod.groupby("day").mean()[y_column]
    df_day = df_day.round(2)
    plot_graph_bar(
        df_day, df_day.index, y_column, f"Produção media de energia por dia do mês({y_column})"
    )

    c1, c2 = st.columns(2)
    with c1:
        df_month = df_prod.groupby("month").agg({y_column: "sum", "month_name": "first"})
        plot_graph_bar(
            df_month,
            df_month["month_name"],
            y_column,
            f"Produção total de energia por mês: {y_column}",
        )

    with c2:
        df_week = df_prod.groupby("weekday").agg({y_column: "mean", "day_name": "first"})
        df_week = df_week.round(2)
        plot_graph_bar(
            df_week,
            df_week["day_name"],
            y_column,
            f"Produção media de energia por dia da semana: {y_column}",
        )

    st.write(" ")
    st.markdown("---")

    plot_go_scatter(df_prod, "date_time", y_column, f"Produção de Energia {y_column}")


def main():
    logger.info("Iniciando main")
    logo = Image.open(settings.ROOT_DIR / "assets" / "unb_logo.jpeg")
    st.sidebar.title("UnB - Solar Production")
    st.sidebar.image(logo, use_column_width=True)

    load_data()
    dashboard()
