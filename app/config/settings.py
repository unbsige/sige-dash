from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
print("=" * 50)
print(f"ROOT_DIR: {ROOT_DIR}")
print("=" * 50)
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
    "uac_avg"
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

WEATHER_FEATURES = [
    "temp", 
    "pressure", 
    "humidity", 
    "wind_speed", 
    "clouds"
]

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
    "time_since_2",]

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
    "lag_std"
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
    1 : {"ip": "164.41.20.230", "group": 2, "col": "uac_1", "name": "UAC 2"},
    2 : {"ip": "164.41.20.231", "group": 2, "col": "uac_2", "name": "UAC 3"},
    3 : {"ip": "164.41.20.233", "group": 1, "col": "ued_3", "name": "UED 2"},
    4 : {"ip": "164.41.20.234", "group": 1, "col": "ued_4", "name": "UED 3"},
    5 : {"ip": "164.41.20.236", "group": 3, "col": "ldtea_5", "name": "LDTEA 1"},
    6 : {"ip": "164.41.20.237", "group": 3, "col": "ldtea_6", "name": "LDTEA 2"},
    7 : {"ip": "164.41.20.238", "group": 3, "col": "ldtea_7", "name": "LDTEA 3"},
    8 : {"ip": "164.41.20.239", "group": 3, "col": "ldtea_8", "name": "LDTEA 4"},
    9 : {"ip": "164.41.20.241", "group": 5, "col": "masp_9", "name": "MASP 1"},
}

PLANT_GROUPS = {
    "ued": 1,
    "uac": 2,
    "ldtea": 3,
    "masp": 4
}
