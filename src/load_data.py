import logging
from pathlib import Path

import pandas as pd
import streamlit as st

from config import settings

logger = logging.getLogger("solar_app")


@st.cache_resource
def load_dataset(filepath, freq):
    logger.info(f"Carregando dados: {filepath}")

    df = pd.read_csv(filepath, parse_dates=["date_time"])
    df.set_index("date_time", inplace=True)
    df = df.sort_index()
    return df.asfreq(freq)


def load_process_data(file_name, freq, df_name):
    file_path = Path(settings.CUR_DATA_DIR / file_name)

    if not file_path.exists():
        logger.error(f"Arquivo {file_path} não encontrado")
        st.error(f"Arquivo {file_path} não encontrado")
        st.stop()

    df = load_dataset(file_path, freq)
    df.columns = df.columns.str.replace(" ", "_").str.lower()

    if df_name == "df_prod":
        df = add_time_features(df)

    return df.sort_index()


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


def load_data():
    logger.info("Iniciando load_data")
    # st.sidebar.subheader("Dados")
    # st.sidebar.markdown(
    #     """
    #     Os dados utilizados neste projeto foram coletados por meio de um sistema de monitoramento de uma usina solar
    #     fotovoltaica localizada no campus Gama da Universidade de Brasília (UnB). O sistema de monitoramento
    #     é composto por 6 medidores de energia (LDTEA 1, LDTEA 2, LDTEA 3, LDTEA 4, UAC 2 e UAC 3). Os dados foram coletados 
    #     a cada 15 minutos no período de 01/06/2023 a 30/09/2023.
    #     """
    # )

    # st.sidebar.markdown(
    #     """
    #     **Fonte dos dados:** [UnB Solar](https://unbsolar.unb.br/monitoramento)
    #     """
    # )

    freq = settings.FREQUENCY
    if "df_prod" not in st.session_state:
        file_name = "data_energy_p60m.csv"
        st.session_state.df_prod = load_process_data(file_name, freq, "df_prod")

    if "df_rad" not in st.session_state:
        file_name = "data_radiation_p60m.csv"
        st.session_state.df_rad = load_process_data(file_name, freq, "df_rad")

    if "df_wth" not in st.session_state:
        file_name = "data_weather_p60m.csv"
        st.session_state.df_wth = load_process_data(file_name, freq, "df_wth")
