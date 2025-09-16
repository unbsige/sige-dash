from pathlib import Path

from environs import Env

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

env = Env()
env_file = ROOT_DIR / ".env"


thermo_irradiance = ["gti_net", "csi_mean", "cell_temp_mean", "day_of_year_cos", "season", "day_since"]

xgb_params = {
    "objective": "reg:absoluteerror",
    "learning_rate": 0.04,
    "max_depth": 4,
    "min_child_weight": 4,
    "subsample": 0.75,
    "colsample_bytree": 0.8,
    "colsample_bylevel": 0.8,
    "reg_alpha": 0.2,
    "reg_lambda": 0.15,
    "gamma": 0.2,
    "n_estimators": 400,
    "early_stopping_rounds": 40,
}


ML_CONFIG = {
    "START_DATE": "2022-03-01",
    "END_DATE": "2024-12-31",
    "FEATURES": thermo_irradiance,
    "XGB_PARAMS": xgb_params,
    "TARGET_COL": "energy",
    "FREQUENCY": "D",
}

env.read_env(env_file)

API_KEYS = {
    "openweather": env.str("API_KEY_OWM"),
    "solcast": env.str("API_KEY_SOLCAST"),
}

GEOLOCATION = {
    "lat": env.float("LAT", -15.7997),
    "lon": env.float("LON", -47.8645),
}

INVERTERS = {
    "canadian": {
        "base_url": "https://webmonitoring-gl.csisolar.com",
        "url_login": "/home/login",
        "url_daily": "/home/maintain-s/history/power/{{device_id}}/record",
        "url_monthly": "/home/maintain-s/history/power/{{device_id}}/stats/monthly",
        "url_yearly": "/home/maintain-s/history/power/{{device_id}}/stats/yearly",
    }
}

CREDENTIALS = {
    "ued": {
        "username": env.str("USERNAME_UED"),
        "password": env.str("PASSWORD_UED"),
    },
    "ldtea": {
        "username": env.str("USERNAME_LDTEA"),
        "password": env.str("PASSWORD_LDTEA"),
    },
    "fce_ued": {
        "username": env.str("USERNAME_FCE_UED"),
        "password": env.str("PASSWORD_FCE_UED"),
    },
}

PLANTS_CONFIG = {
    "fcte_ued": {
        "name": "Faculdade de Ciências e Tecnologias em Engenharia - Campus UnB Gama",
        "acronym": "FCTE UED",
        "location": "Unidade de Ensino e Docência",
        "installed_capacity": 125.0,
        "inverter_model": "canadian",
        "credentials": "ued",
        "device_id": env.str("DEVICE_ID_UED"),
        "latitude": env.float("LAT"),
        "longitude": env.float("LON"),
        "azimuth": 0,
        "tilt": 16,
        "module_type": "mono-si",
        "noct": 42.0,
        "temp_coeff": -0.0037,
        "irrad_coeff": 0.031,
        "csv_file": "pv_data_ued.csv",
        "devices": [
            {
                "id": env.str("DEVICE_ID_UED"),
                "name": "UED",
                "capacity": 62.5,
                "model": "CSI-50KTL",
                "serial_number": "",
            },
        ],
    },
    "fcte_ldtea": {
        "name": "Laboratório de Desenvolvimento de Tecnologias para Energia Alternativa e MASP",
        "acronym": "LDTEA e MASP",
        "location": "Campus UnB Gama",
        "installed_capacity": 202.0,
        "inverter_model": "canadian",
        "credentials": "ldtea",
        "device_id": env.str("DEVICE_ID_LDTEA_MASP"),
        "latitude": env.float("LAT"),
        "longitude": env.float("LON"),
        "azimuth": 0,
        "tilt": 16,
        "module_type": "mono-si",
        "noct": 42.0,
        "temp_coeff": -0.0037,
        "irrad_coeff": 0.031,
        "csv_file": "fcte_ldtea_data.csv",
        "devices": [],
    },
    "fce_ued": {
        "name": "Unidade de Ensino e Docência - FCE",
        "acronym": "FCE UED",
        "location": "Faculdade de Ciências Econômicas - Campus UnB Gama",
        "installed_capacity": 50.0,
        "inverter_model": "canadian",
        "credentials": "fce_ued",
        "device_id": env.str("DEVICE_ID_FCE_UED"),
        "latitude": env.float("LAT"),
        "longitude": env.float("LON"),
        "devices": [
            {
                "id": env.str("DEVICE_ID_FCE_UED"),
                "name": "UED FCE",
                "capacity": 50.0,
                "model": "CSI-50KTL",
                "serial_number": "",
            },
        ],
    },
}

DATA_DIR = ROOT_DIR / "data"
CUR_DATA_DIR = DATA_DIR / "current"
CLEAN_DATA_DIR = DATA_DIR / "clean"
RAW_DATA_DIR = DATA_DIR / "raw"
FINAL_DATA_DIR = DATA_DIR / "final"
LOG_DIR = ROOT_DIR / "logs"
SRC_DIR = ROOT_DIR / "src"

FREQUENCY = "h"
DATE_COL = "date_time"
PLANTS = ["LDTEA", "UAC", "UED", "MASP"]
AGG_TARGETS = ["ldtea_avg", "ldtea_total", "uac_total", "uac_avg"]
TARGETS = [
    "ldtea_5",
    "ldtea_6",
    "ldtea_7",
    "ldtea_8",
    "uac_1",
    "uac_2",
    "ldtea_avg",
    "ldtea_total",
    "uac_total",
    "uac_avg",
]

START_DATE = "2023-06-01 00:00:00"
SPLIT_TEST_DATE = "2024-03-19 23:59:59"
SPLIT_DATE_EVAL = "2024-05-31 23:59:59"
END_DATE = "2024-06-15 23:59:59"

LAGS = [1, 24, 48, 72, 96]
WINDOWS = [3, 6, 12, 24]

IRRADIATION_FEATURES = [
    "air_temp",
    "ghi",
    "gti",
]

WEATHER_FEATURES = ["temp", "pressure", "humidity", "wind_speed", "clouds"]

TIME_FEATURES = [
    "hour",
    "day",
    "month",
    "day_of_week",
    "is_weekend",
    "is_night",
]

CYCLIC_FEATURES = [
    "hour_sin",
    "hour_cos",
    "day_sin",
    "day_cos",
    "day_of_week_sin",
    "day_of_week_cos",
]

SINCE_FEATURES = [
    "time_since",
    "time_since_2",
]

RADIAL_FEATURES = [
    "rbf_0",
    "rbf_1",
    "rbf_2",
    "rbf_3",
    "rbf_4",
    "rbf_5",
    "rbf_6",
    "rbf_7",
    "rbf_8",
    "rbf_9",
    "rbf_10",
    "rbf_11",
]

LAG_FEATURES = [
    "lag1",
    "lag24",
    "lag48",
    "lag72",
    "lag96",
    "lag_mean",
    "lag_median",
    "lag_std",
]

WINDOWS_FEATURES = [
    "window3_mean",
    "window3_median",
    "window3_std",
    "window3_min",
    "window3_max",
    "window6_mean",
    "window6_median",
    "window6_std",
    "window6_min",
    "window6_max",
    "window12_mean",
    "window12_median",
    "window12_std",
    "window12_min",
    "window12_max",
    "window24_mean",
    "window24_median",
    "window24_std",
    "window24_min",
    "window24_max",
]

IS_WEEKEND_MAP = {0: "Dia da Semana", 1: "Fim de Semana"}

DAY_MAPPING = {
    0: "Domingo",
    1: "Segunda-feira",
    2: "Terça-feira",
    3: "Quarta-feira",
    4: "Quinta-feira",
    5: "Sexta-feira",
    6: "Sábado",
}

MONTH_MAPPING = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Março",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro",
}

INVERTER_MAPPING = {
    1: {"ip": "164.41.20.230", "group": 2, "col": "uac_1", "name": "UAC 2"},
    2: {"ip": "164.41.20.231", "group": 2, "col": "uac_2", "name": "UAC 3"},
    3: {"ip": "164.41.20.233", "group": 1, "col": "ued_3", "name": "UED 2"},
    4: {"ip": "164.41.20.234", "group": 1, "col": "ued_4", "name": "UED 3"},
    5: {"ip": "164.41.20.236", "group": 3, "col": "ldtea_5", "name": "LDTEA 1"},
    6: {"ip": "164.41.20.237", "group": 3, "col": "ldtea_6", "name": "LDTEA 2"},
    7: {"ip": "164.41.20.238", "group": 3, "col": "ldtea_7", "name": "LDTEA 3"},
    8: {"ip": "164.41.20.239", "group": 3, "col": "ldtea_8", "name": "LDTEA 4"},
    9: {"ip": "164.41.20.241", "group": 5, "col": "masp_9", "name": "MASP 1"},
}

PLANT_GROUPS = {"ued": 1, "uac": 2, "ldtea": 3, "masp": 4}
