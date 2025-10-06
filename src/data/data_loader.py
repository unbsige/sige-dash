from pathlib import Path

import pandas as pd
import streamlit as st

from src.collectors.csi_utils import get_or_create_client, process_energy_statistics, process_power_records
from src.config import settings


@st.cache_data(ttl=1800)
def get_plant_data(plant, start_date, end_date=None, granularity="daily"):
    """Fetch power data for a specific plant and device."""

    plant_key = plant.get("code")
    device_id = plant.get("device", {}).get("id")

    if not device_id:
        st.error(f"Device ID not found for plant: {plant_key}")
        return None

    try:
        client = get_or_create_client(plant)
        if not client:
            st.error(f"Failed to create client for plant: {plant['code']}")
            return None

        if not start_date:
            st.error("Start date is required.")
            return None

        if end_date:
            response_data = client.get_power_range(device_id, start_date, end_date, granularity=granularity)
        else:
            response_data = client.get_power_data_daily(device_id, start_date)
            response_data = [{"date": start_date, "data": response_data}]

        return response_data

    except Exception as e:
        st.error(f"Error fetching data for {plant_key}: {str(e)}")
        session_key = f"client_{plant_key}"
        if session_key in st.session_state:
            del st.session_state[session_key]
        return None


# @st.cache_data(ttl=1800)
# def get_all_plants_data(start_date, end_date, granularity="daily"):
#     """Fetch data for all available plants."""

#     all_data = {}
#     available_plants = get_available_plants()

#     for plant_key, plant_config in available_plants.items():
#         device_id = plant_config["device"].get("device_id")
#         if not device_id:
#             continue

#         response_data = get_plant_data(plant_key, device_id, start_date, end_date, granularity)

#         if response_data:
#             df_stats = process_energy_statistics(response_data)
#             if not df_stats.empty:
#                 all_data[plant_key] = {
#                     "config": plant_config,
#                     "device_id": device_id,
#                     "data": df_stats,
#                 }

#     return all_data


@st.cache_data(ttl=1800)  # Cache por 5 minutos
def get_daily_data(plant, selected_date):
    try:
        data = get_plant_data(plant, selected_date, granularity="daily")
        if data:
            return {"power": process_power_records(data), "energy": process_energy_statistics(data)}
        return None
    except Exception as e:
        st.error(f"Erro ao buscar dados da API: {str(e)}")
        return None


@st.cache_data(ttl=3600)
def load_historical_data(plant, freq="1d"):
    freq_map = {"1d": "pt1d", "pt1d": "pt1d", "5m": "pt5m", "5min": "pt5m", "pt5m": "pt5m"}

    if freq not in freq_map:
        st.error(f"Invalid frequency: {freq}. Use '1d' or '5m'.")
        return pd.DataFrame()

    _freq = freq_map[freq]
    file_name = f"{plant.get('code')}_{_freq}.csv"
    csv_path = Path(settings.DASH_DATA_DIR / file_name)

    print(f"Loading historical data from: {csv_path}")

    try:
        if csv_path.exists():
            return pd.read_csv(csv_path, index_col=0, parse_dates=True)

        st.warning(f"Arquivo histórico não encontrado: {csv_path}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao carregar dados históricos: {str(e)}")
        return pd.DataFrame()
