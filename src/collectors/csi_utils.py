from datetime import datetime, timedelta

import pandas as pd
import streamlit as st
from plotly import graph_objects as go

from src.collectors.csi_oauth_client import CSISolarOAuthClient
from src.collectors.csi_solar_client import CSISolarClient
from src.config.settings import BR_TZ, CREDENTIALS, DEVICE_IDS, INVERTERS_URLS


def get_urls_with_device_id(inverter_model, device_id):
    inverter = INVERTERS_URLS[inverter_model]

    return {
        "base_url": inverter["base_url"],
        "url_login": inverter["url_login"],
        "url_daily": inverter["url_daily"].replace("{{device_id}}", device_id),
        "url_monthly": inverter["url_monthly"].replace("{{device_id}}", device_id),
    }


def get_or_create_client(plant):
    plant_key = plant.get("code")
    creds = plant.get("credentials", {})
    device = plant.get("device", {})
    inverter_model = device.get("model")

    session_key = f"client_{plant['code']}"
    base_url = INVERTERS_URLS[inverter_model]["base_url"]

    try:
        with st.spinner(f"Conectando com {plant_key}..."):
            oauth_client = CSISolarOAuthClient(base_url=base_url)
            response_data = oauth_client.login(creds["username"], creds["password"])

            if not response_data:
                st.error(f"Falha no login para {plant_key}")
                return None

            client = CSISolarClient(token=oauth_client.access_token, base_url=base_url)

            st.session_state[session_key] = client
            st.session_state[f"token_time_{session_key}"] = datetime.now()
            return client

    except Exception as e:
        st.error(f"Erro ao conectar com {plant_key}: {str(e)}")
        return None


def process_power_records(response_data, timezone_br=BR_TZ):
    def create_dataframe_power_records(data, columns=None):
        if columns is None:
            return pd.DataFrame()

        all_records = []
        for entry in data:
            records_data = entry.get("data", {}).get("records", [])
            if records_data:
                for record in records_data:
                    filtered_record = {col: record.get(col) for col in columns if col in record}
                    if filtered_record:
                        all_records.append(filtered_record)

        return pd.DataFrame(all_records) if all_records else pd.DataFrame()

    records_columns = ["dateTime", "timeZoneOffset", "generationPower", "generationCapacity"]
    df_power_raw = create_dataframe_power_records(response_data, columns=records_columns)

    if df_power_raw.empty:
        return pd.DataFrame()

    df_power = df_power_raw.copy()
    df_power["date_time"] = pd.to_datetime(df_power["dateTime"], unit="s", utc=True)
    df_power["date_time"] = df_power["date_time"].dt.tz_convert(timezone_br)
    df_power.set_index("date_time", inplace=True)
    df_power.sort_index(inplace=True)

    df_power.drop(columns=["dateTime", "timeZoneOffset"], inplace=True)
    df_power.rename(columns={"generationPower": "pv_power", "generationCapacity": "pv_capacity"}, inplace=True)
    df_power["pv_power"] = df_power["pv_power"] / 1000.0

    return df_power


def process_energy_statistics(response_data):
    def create_dataframe_energy_statistics(data, columns=None):
        if columns is None:
            return pd.DataFrame()

        all_statistics = []
        for entry in data:
            statistics_data = entry.get("data", {}).get("statistics", {})
            if statistics_data:
                filtered_stats = {col: statistics_data.get(col) for col in columns if col in statistics_data}
                if filtered_stats:
                    all_statistics.append(filtered_stats)

        return pd.DataFrame(all_statistics) if all_statistics else pd.DataFrame()

    statistics_columns = ["generationValue", "incomeValue", "fullPowerHoursDay", "acceptDay"]
    stats_df_raw = create_dataframe_energy_statistics(response_data, columns=statistics_columns)

    if stats_df_raw.empty:
        return pd.DataFrame()

    stats_df = stats_df_raw.copy()
    stats_df.rename(
        columns={
            "acceptDay": "date",
            "fullPowerHoursDay": "full_power_hours",
            "generationValue": "pv_energy",
            "incomeValue": "income_value",
        },
        inplace=True,
    )
    stats_df["date"] = pd.to_datetime(stats_df["date"], format="%Y%m%d").dt.date
    stats_df.set_index("date", inplace=True)
    stats_df.sort_index(inplace=True)

    return stats_df


def plot_pv_power_time_series(df, title=None, power_column="pv_power", width=1800, height=500):
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df[power_column],
            name="Potência PV (kW)",
            mode="lines",
            line={"color": "#2E86AB", "width": 1.2},
            opacity=0.85,
        )
    )

    fig.update_layout(
        title=title or "Série Temporal da Potência Fotovoltaica",
        xaxis_title="Data",
        yaxis_title="Potência (kW)",
        width=width,
        height=height,
        plot_bgcolor="#FAFAFA",
        paper_bgcolor="#FAFAFA",
        font={"size": 14},
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
            "font": {"size": 13},
        },
        margin={"l": 40, "r": 40, "t": 60, "b": 40},
    )
    return fig
