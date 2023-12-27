from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT_DIR / "data"
CUR_DATA_DIR = DATA_DIR / "current"
BKP_DATA_DIR = DATA_DIR / "backups"
LOG_DIR = ROOT_DIR / "logs"
SRC_DIR = ROOT_DIR / "src"

FREQUENCY = "H"
DATE_COL = "date_time"
TARGET = "ldtea_avg"
TARGET_AGG = ["ldtea_avg", "uac_avg"]
TARGETS = ["ldtea1", "ldtea2", "ldtea3", "ldtea4", "uac2", "uac3"]

START_DATE = pd.to_datetime("2023-06-01 00:00:00")
SPLIT_DATE = pd.to_datetime("2023-09-15 23:59:59")
END_DATE = pd.to_datetime("2023-09-30 23:59:59")

LAGS = [1, 24, 48, 72, 96]
WINDOWS = [3, 6, 12, 24]

IRRAD_FEATURES = [
    "air_temp",
    "dni",
    "ghi",
    "dhi",
    "gti",
    "clearsky_dhi",
    "clearsky_ghi",
    "clearsky_gti",
    "clearsky_dni",
    "cloud_opacity",
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
