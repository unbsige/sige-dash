from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT_DIR / "data"
LOG_DIR = ROOT_DIR / "logs"
SRC_DIR = ROOT_DIR / "src"

TARGET = "ldtea"
DATE_COL = "date_time"
FREQUENCY = "H"

START_DATE = pd.to_datetime("2023-06-01 00:00:00")
SPLIT_DATE = pd.to_datetime("2023-09-15 23:59:59")
END_DATE = pd.to_datetime("2023-09-30 23:59:59")


TIME_FEATURES = [
    "hour",
    "day",
    "month",
    "weekday",
    "weekend",
    "is_night",
]

TARGET_COLS = [
    "ldtea_avg",
    "ldtea_1",
    "ldtea_2",
    "ldtea_3",
    "ldtea_4",
    "uac_avg",
    "uac_2",
    "uac_3",
]

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
