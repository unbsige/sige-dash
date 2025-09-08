import pandas as pd
import pytz
from plotly import graph_objects as go

from app.config.settings import INVERTERS

BR_TZ = pytz.timezone("America/Sao_Paulo")
UTC_TZ = pytz.timezone("UTC")


def get_urls_with_device_id(inverter_model, device_id):
    inverter = INVERTERS[inverter_model]

    return {
        "base_url": inverter["base_url"],
        "url_login": inverter["url_login"],
        "url_daily": inverter["url_daily"].replace("{{device_id}}", device_id),
        "url_monthly": inverter["url_monthly"].replace("{{device_id}}", device_id),
    }


def create_records_dataframe(data, columns=None):
    if columns is None:
        print("Nenhuma coluna especificada para registros.")
        return pd.DataFrame()

    all_records = []
    for entry in data:
        records_data = entry.get("data", {}).get("records", [])
        if records_data:
            for record in records_data:
                filtered_record = {
                    col: record.get(col) for col in columns if col in record
                }
                if filtered_record:
                    all_records.append(filtered_record)

    return pd.DataFrame(all_records) if all_records else pd.DataFrame()


def create_statistics_dataframe(data, columns=None):
    if columns is None:
        print("Nenhum coluna especificada para estatísticas.")
        return pd.DataFrame()

    all_statistics = []
    for entry in data:
        statistics_data = entry.get("data", {}).get("statistics", {})
        if statistics_data:
            filtered_stats = {
                col: statistics_data.get(col)
                for col in columns
                if col in statistics_data
            }
            if filtered_stats:
                all_statistics.append(filtered_stats)

    return pd.DataFrame(all_statistics) if all_statistics else pd.DataFrame()


def process_power_records(response_data, timezone_br=BR_TZ):
    records_columns = [
        "dateTime",
        "timeZoneOffset",
        "generationPower",
        "generationCapacity",
    ]
    rec_df_raw = create_records_dataframe(response_data, columns=records_columns)
    rec_df = rec_df_raw.copy()

    if rec_df.empty:
        raise ValueError("Nenhum registro encontrado nos dados fornecidos.")

    timezones = rec_df["timeZoneOffset"].unique()
    print(f"Timezones detectados: {timezones}")

    rec_df["date_time"] = pd.to_datetime(rec_df["dateTime"], unit="s", utc=True)
    rec_df["date_time"] = rec_df["date_time"].dt.tz_convert(timezone_br)
    rec_df.set_index("date_time", inplace=True)
    rec_df.sort_index(inplace=True)

    columns_to_drop = ["dateTime", "timeZoneOffset"]
    rec_df.drop(columns=columns_to_drop, inplace=True)

    rec_df.rename(
        columns={"generationPower": "pv_power", "generationCapacity": "pv_capacity"},
        inplace=True,
    )
    rec_df["pv_power"] = rec_df["pv_power"] / 1000.0

    print(f"Total de registros: {len(rec_df)}")
    return rec_df


def process_statistics(response_data):
    statistics_columns = [
        "generationValue",
        "incomeValue",
        "fullPowerHoursDay",
        "acceptDay",
    ]
    stats_df_raw = create_statistics_dataframe(
        response_data, columns=statistics_columns
    )

    stats_df = stats_df_raw.copy()
    stats_df.rename(
        columns={
            "acceptDay": "date",
            "fullPowerHoursDay": "full_power_hours",
            "generationValue": "generation_value",
            "incomeValue": "income_value",
        },
        inplace=True,
    )
    stats_df["date"] = pd.to_datetime(stats_df["date"], format="%Y%m%d").dt.date
    stats_df.set_index("date", inplace=True)
    stats_df.sort_index(inplace=True)

    return stats_df


def plot_pv_power_time_series(
    df, title=None, power_column="pv_power", width=1800, height=500
):
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
