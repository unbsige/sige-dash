import logging
from pathlib import Path

import pandas as pd
import streamlit as st

from config import settings

logger = logging.getLogger("solar_app")


@st.cache_data
def load_dataset(filepath, freq, columns=None):
    logger.info(f"Carregando dados: {filepath}")

    if columns:
        df = pd.read_csv(filepath, parse_dates=["date_time"], usecols=["date_time"] + columns)
    else:
        df = pd.read_csv(filepath, parse_dates=["date_time"])

    df = df.set_index("date_time")
    df.index = df.index.tz_localize(None)
    df = df.sort_index()
    # return df.asfreq(freq)
    return df


def load_plant_data(plant_key, freq, columns=None):
    plant_config = settings.PLANTS_CONFIG.get(plant_key)
    if not plant_config:
        logger.error(f"Planta {plant_key} não encontrada na configuração")
        st.error(f"Planta {plant_key} não encontrada na configuração")
        st.stop()

    filename = plant_config.get("data_source", {}).get("file")
    filename_parts = filename.split(".")
    filename = f"{filename_parts[0]}_{freq}.{filename_parts[1]}"
    filepath = Path(settings.FINAL_DATA_DIR / filename)

    if not filepath.exists():
        logger.error(f"Arquivo {filepath} não encontrado")
        st.error(f"Arquivo {filepath} não encontrado")
        st.stop()

    df = load_dataset(filepath, freq, columns=columns)
    df = load_dataset(filepath, freq)
    return df


def load_process_data(file_name, freq, df_name):
    file_path = Path(settings.FINAL_DATA_DIR / file_name)

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

    freq = settings.FREQUENCY
    if "df_prod" not in st.session_state:
        file_name = "1.0_energy_prod_all.csv"
        df_prod = load_process_data(file_name, freq, "df_prod")
        st.session_state.df_prod = df_prod

    if "df_rad_tempook" not in st.session_state:
        file_name = "0.1_radiation_tempook_p60m.csv"
        st.session_state.df_rad_tempook = load_process_data(file_name, freq, "df_rad_tempook")

    if "df_rad_solcast" not in st.session_state:
        file_name = "0.2_radiation_solcast_p60m.csv"
        st.session_state.df_rad_solcast = load_process_data(file_name, freq, "df_rad_solcast")


def get_plant_defaults(plant_config):
    df_losses = {
        "soiling": 0.025,  # 2.5% - maior devido ao clima seco
        "shading": 0.005,  # 0.5% - campus aberto
        "mismatch": 0.020,  # 2.0% - módulos comerciais
        "dc_wiring": 0.015,  # 1.5% - distâncias médias
        "aging": 0.008,  # 0.8% - degradação por ano
        "diodes": 0.001,  # 0.1% - perdas mínimas
    }

    tech_behavior = {"mono-si": -0.028, "poly-si": -0.031, "perc": -0.025}

    module_type = plant_config.get("module_type", "poly-si")

    return {
        "a0": sum(df_losses.values()),
        "a1": tech_behavior.get(module_type, -0.031),
        "a2": abs(plant_config["temp_coeff"]) * 0.8,  # Perdas térmicas não-lineares
        "k0": 0.0018,  # Canadian Solar típico
        "k1": 0.0082,
        "k2": 0.0195,
    }
