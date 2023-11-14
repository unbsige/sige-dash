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

@st.cache_resource
def load_dataset(filepath, frequency):
    logger.info("Carregando dados de produção de energia")

    df = pd.read_csv(filepath, parse_dates=["date_time"])
    df.set_index("date_time", inplace=True)
    df = df.sort_index()
    df = df.asfreq(frequency)
    return df


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


def plot_graph_line(df, x, y, title):
    fig = px.line(df, x=x, y=y, template='simple_white', title=f'<b>{title}</b>')
    fig.update_traces(line_color='#A27D4F')
    # fig.update_traces(fill='tozeroy', fillcolor='#333333', opacity=0.1)
    fig.update_layout(
        xaxis=dict(showgrid=True, gridwidth=0.1),
        yaxis=dict(showgrid=True, gridwidth=0.1)
    )
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    return fig


def plot_graph_bar(df, x_column, y_column, title):
    fig = px.bar(
        df,
        x=x_column,
        y=y_column,
        template='simple_white',
        barmode="group",
        title=f'<b>{title}</b>',
        text=y_column,
        hover_name=y_column
    )
    fig.update_traces(marker_color='#A27D4F', textposition='outside', hovertemplate='%{x}: %{y} kWh')
    fig.update_traces(marker_color='#A27D4F')
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    fig.update_yaxes(showgrid=True, gridwidth=0.1)
    fig.update_xaxes(title_text="")
    fig.update_yaxes(title_text="Energy Production (kWh)")
    return fig


def run_app():
    logger.info("Iniciando run_app")

    freq = settings.FREQUENCY
    file_path = Path(settings.FILEPATH)

    if not file_path.exists():
        logger.error("Arquivo %s não encontrado", file_path)
        st.error(f"Arquivo {file_path} não encontrado")
        return

    df_raw = load_dataset(file_path, freq)
    df_agg = aggregate_ldtea(df_raw)
    df = add_time_features(df_agg)
    df.sort_index(inplace=True)

    st.session_state.df = df
    st.session_state.file_path = file_path

    # ============================================================================================================================

    st.title("Energy Production ⚡")
    st.subheader("Dataframes")

    col1, col2 = st.columns(2)
    with col1.expander("Energy Production raw data"):
        st.dataframe(df_raw)

    with col2.expander("Energy Production aggregated data"):
        st.dataframe(df_agg)

    df_day = df.groupby("day").mean()["avg_ldtea"]
    with col1.expander("Avg Energy Production by day"):
        st.dataframe(df_day)

    df_month_avg = df.groupby("month_name").mean()["avg_ldtea"]
    with col2.expander("Avg Energy Production by Month"):
        st.dataframe(df_month_avg)

    with st.expander("Energy Production data"):
        st.dataframe(df)

    # =================================================================================================================
    st.write(" ")
    st.markdown("---")
    st.subheader("Graficos")
    st.sidebar.subheader("Filtros")

    cols = df_agg.columns
    y_column = st.sidebar.selectbox(
        "Selecione o medidor",
        cols,
        key="y_column",
        help="Selecione o medidor para visualizar os gráficos"
    )

    c1, *_ = st.columns(4)
    months = df["month_name"].unique()
    month = c1.selectbox(
        "Selecione o mês",
        months,
        key="month",
        help="Selecione o mês para visualizar os gráficos"
    )

    df_month = df[df["month_name"] == month]
    fig = plot_graph_line(df_month, df_month.index, y_column, f"Energy Production: {y_column}")
    st.plotly_chart(fig, use_container_width=True)

    st.write(" ")
    c1, c2, *_ = st.columns(4)
    start_date = c1.date_input("Data inicial", value=df.index.min())
    end_date = c2.date_input("Data final", value=df.index.max())

    df_date = df.loc[start_date:end_date]
    fig = plot_graph_line(df_date, df_date.index, y_column, f"Energy Production {y_column}: {start_date} - {end_date}")
    st.plotly_chart(fig, use_container_width=True)

    # adicionar ao agrupamento um roud de duas casas
    df_day = df.groupby("day").mean()[y_column]
    df_day = df_day.round(2)
    fig = plot_graph_bar(df_day, df_day.index, y_column, f"Producao media horaria {y_column} by Day")
    st.plotly_chart(fig, use_container_width=True)

    df_month = df.groupby("month").agg({y_column: 'sum', 'month_name': 'first'})
    fig = plot_graph_bar(df_month, df_month["month_name"], y_column, f"Producao total de energia por mes: {y_column}")
    st.plotly_chart(fig, use_container_width=True)
