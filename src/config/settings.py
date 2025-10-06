from datetime import datetime, timedelta
from pathlib import Path

import pytz
from environs import Env

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

env = Env()
env_file = ROOT_DIR / ".env"

if env_file.exists():
    env.read_env(env_file)


# DATA DIRECTORIES
# --------------------------------------------------------------------------------------
DATA_DIR = ROOT_DIR / "data"
CUR_DATA_DIR = DATA_DIR / "current"
CLEAN_DATA_DIR = DATA_DIR / "clean"
RAW_DATA_DIR = DATA_DIR / "raw"
RESULT_DATA_DIR = DATA_DIR / "result"
DASH_DATA_DIR = DATA_DIR / "dash"
LOG_DIR = ROOT_DIR / "logs"
SRC_DIR = ROOT_DIR / "src"


# TIMEZONE CONFIGURATION AND FORMATTING
# --------------------------------------------------------------------------------------

BR_TZ_NAME = "America/Sao_Paulo"
BR_TZ_OFFSET = timedelta(hours=-3)
BR_TZ = pytz.timezone(BR_TZ_NAME)

UTC_TZ_NAME = "UTC"
UTC_TZ_OFFSET = timedelta(hours=0)
UTC_TZ = pytz.timezone(UTC_TZ_NAME)

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M:%S"


# MLFlow Configuration
# --------------------------------------------------------------------------------------
MLFLOW_CONFIG = {
    "tracking_uri": env.str("MLFLOW_TRACKING_URI", "sqlite:///mlflow_playground.db"),
    "experiment_prefix": "PV_Playground",
    "artifact_location": str(ROOT_DIR / "mlflow_artifacts"),
    "default_experiment": "Default",
}


# ML MODEL PARAMETERS
# --------------------------------------------------------------------------------------
DEFAULT_MODEL_PARAMS = {
    "xgboost": {
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
    },
    "physics": {
        "apply_losses": True,
        "inverter_efficiency": 0.95,
        "use_advanced_losses": False,
    },
}

thermo_irradiance = [
    "gti_net",
    "csi_mean",
    "cell_temp_mean",
    "day_of_year_cos",
    "season",
    "day_since",
]

ML_CONFIG = {
    "START_DATE": "2022-03-01",
    "END_DATE": "2024-12-31",
    "FREQUENCY": "D",
    "TARGET_COL": "energy",
    "DATE_COL": "date_time",
    "DATA_PATH": str(ROOT_DIR / "data"),
    "DATE_SPLIT": {
        "train_start": "2022-03-01",
        "train_end": "2023-10-31",
        "test_start": "2023-11-01",
        "test_end": "2024-12-31",
    },
    "XGB": {
        "FEATURES": thermo_irradiance,
        "XGB_PARAMS": DEFAULT_MODEL_PARAMS["xgboost"],
    },
    "PHYSICS": {
        "FEATURES": ["gti", "air_temp"],
        "PARAMS": DEFAULT_MODEL_PARAMS["physics"],
    },
}

EXTERNAL_APIS = {
    "openweather": {
        "api_key": env.str("API_KEY_OWM", ""),
        "base_url": "https://api.openweathermap.org/data/2.5",
        "rate_limit": 1000,  # calls per day
    },
    "solcast": {
        "api_key": env.str("API_KEY_SOLCAST", ""),
        "base_url": "https://api.solcast.com.au",
        "rate_limit": 50,  # calls per day
    },
}

INVERTERS_URLS = {
    "canadian_solar": {
        "base_url": "https://webmonitoring-gl.csisolar.com",
        "url_login": "/home/login",
        "url_daily": "/home/maintain-s/history/power/{{device_id}}/record",
        "url_monthly": "/home/maintain-s/history/power/{{device_id}}/stats/monthly",
        "url_yearly": "/home/maintain-s/history/power/{{device_id}}/stats/yearly",
    }
}

CREDENTIALS = {
    "fcte_ued": {
        "username": env.str("USERNAME_FCTE_UED"),
        "password": env.str("PASSWORD_FCTE_UED"),
    },
    "fcte_ldtea": {
        "username": env.str("USERNAME_FCTE_LDTEA"),
        "password": env.str("PASSWORD_FCTE_LDTEA"),
    },
    "fcts_ued": {
        "username": env.str("USERNAME_FCTS_UED"),
        "password": env.str("PASSWORD_FCTS_UED"),
    },
    "dr_ics": {
        "username": env.str("USERNAME_DR_ICS"),
        "password": env.str("PASSWORD_DR_ICS"),
    },
    "dr_ipol_irel": {
        "username": env.str("USERNAME_DR_IPOL_IREL"),
        "password": env.str("PASSWORD_DR_IPOL_IREL"),
    },
}

DEVICE_IDS = {
    "fcte_ued": {
        "model": "canadian_solar",
        "id": env.str("DEVICE_ID_FCTE_UED"),
    },
    "fcte_ldtea": {
        "model": "canadian_solar",
        "id": env.str("DEVICE_ID_FCTE_LDTEA"),
    },
    "fcts_ued": {
        "model": "canadian_solar",
        "id": env.str("DEVICE_ID_FCTS_UED"),
    },
    "dr_ics": {
        "model": "canadian_solar",
        "id": env.str("DEVICE_ID_DR_ICS"),
    },
    "dr_ipol_irel": {
        "model": "canadian_solar",
        "id": env.str("DEVICE_ID_DR_IPOL_IREL"),
    },
}


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


# https://webmonitoring-gl.csisolar.com/home/maintain-s/operating/system/
# https://webmonitoring-gl.csisolar.com/home/maintain-s/history/power/1735533/stats/month?year=2025&month=9 (dia a dia - mes completo)
# https://webmonitoring-gl.csisolar.com/home/maintain-s/history/power/1735533/record?year=2025&month=9&day=7 (a cada 5 minutos - dia especifico)
# https://webmonitoring-gl.csisolar.com/home/maintain-s/history/power/1481452/stats/year?year=2025 (mes a mes - ano completo)
# https://webmonitoring-gl.csisolar.com/home/maintain-s/history/power/1481452/stats/total (ano a ano - desde o inicio)
# https://webmonitoring-gl.csisolar.com/home/region-s/weather/record/month?regionNationId=33&year=2025&month=09&timezone=America%2FSao_Paulo&lan=pt


# Mapa das usinas no Google Maps:
# https://www.google.com/maps/d/viewer?mid=1g-9G1m1D0BguKXhxga7MIc8BjO2S-wo&femb=1&ll=-15.762241972224825%2C-47.87345302759307&z=16
# http://sema.unb.br/efici%C3%AAncia-energ%C3%A9tica

# =====================================================================================================================


PLANTS_CONFIG = {
    "fcte_ued": {
        "name": "FCTE - Unidade de Ensino e Docência",
        "acronym": "FCTE UED",
        "location": "UnB Gama",
        "capacity_kwp": 125.0,
        "noct": 42.0,
        "temp_coeff": -0.0037,
        "irrad_coeff": 0.031,
        "latitude": env.float("LAT", -15.989),
        "longitude": env.float("LON", -48.044),
        "azimuth": 0,
        "tilt": 16,
        "module_type": "mono-si",
        "data_sources": {
            "1d": {
                "type": "csv",
                "file": "pv_energy_fcte_ued_pt1d.csv",
                # "file": "pv_energy_fcte_ued_solar_feat_pt1d.csv",
                "frequency": "1d",
            },
            "5min": {
                "type": "csv",
                "file": "pv_power_fcte_ued_pt5m.csv",
                # "file": "pv_power_fcte_ued_solar_feat_pt5m.csv",
                "frequency": "5t",
            },
        },
        "credentials": {
            "username": env.str("USERNAME_UED", ""),
            "password": env.str("PASSWORD_UED", ""),
            "api_base_url": "https://api.canadiansolar.com",
        },
        "device": {
            "model": "canadian_solar",
            "device_id": env.str("DEVICE_ID_UED", ""),
        },
        "devices": {
            "UED": {
                "model": "canadian_solar",
                "device_id": env.str("DEVICE_ID_UED", ""),
            },
            "ICS": {
                "model": "canadian_solar",
                "device_id": env.str("DEVICE_ID_ICS", ""),
            },
            "IPOL/IREL": {
                "model": "canadian_solar",
                "device_id": env.str("DEVICE_ID_IPOL_IREL", ""),
            },
        },
    },
    "fcte_ldtea": {
        "name": "LDTEA e MASP",
        "acronym": "LDTEA",
        "location": "UnB Gama",
        "capacity_kwp": 202.0,
        "noct": 42.0,
        "temp_coeff": -0.0037,
        "irrad_coeff": 0.031,
        "latitude": env.float("LAT", -15.989),
        "longitude": env.float("LON", -48.044),
        "azimuth": 0,
        "tilt": 16,
        "module_type": "mono-si",
        "data_sources": {
            "1d": {
                "type": "csv",
                "file": "pv_energy_fcte_ldtea_pt1d.csv",
                # "file": "pv_energy_fcte_ldtea_solar_feat_pt1d.csv",
                "frequency": "1d",
            },
            "5min": {
                "type": "csv",
                "file": "pv_power_fcte_ldtea_pt5m.csv",
                # "file": "pv_power_fcte_ldtea_solar_feat_pt5m.csv",
                "frequency": "5t",
            },
        },
        "credentials": {
            "username": env.str("USERNAME_LDTEA", ""),
            "password": env.str("PASSWORD_LDTEA", ""),
            "api_base_url": "https://api.canadiansolar.com",
        },
        "device": {
            "model": "canadian_solar",
            "device_id": env.str("DEVICE_ID_LDTEA_MASP", ""),
        },
        "devices": {
            "LDTEA": {
                "model": "canadian_solar",
                "device_id": env.str("DEVICE_ID_LDTEA_MASP", ""),
            },
            "MASP": {
                "model": "canadian_solar",
                "device_id": env.str("DEVICE_ID_MASP", ""),
            },
        },
    },
    "fce_ued": {
        "name": "FCE - Unidade de Ensino e Docência",
        "acronym": "FCE UED",
        "location": "UnB Gama",
        "capacity_kwp": 50.0,
        "noct": 42.0,
        "temp_coeff": -0.0037,
        "irrad_coeff": 0.031,
        "latitude": env.float("LAT", -15.989),
        "longitude": env.float("LON", -48.044),
        "azimuth": 0,
        "tilt": 16,
        "module_type": "mono-si",
        "data_sources": {
            "1d": {
                "type": "csv",
                "file": "pv_energy_fce_ued_pt1d.csv",
                # "file": "pv_energy_fce_ued_solar_feat_pt1d.csv",
                "frequency": "1d",
            },
            "5min": {
                "type": "csv",
                "file": "pv_power_fce_ued_pt5m.csv",
                # "file": "pv_power_fce_ued_solar_feat_pt5m.csv",
                "frequency": "5t",
            },
        },
        "credentials": {
            "username": env.str("USERNAME_FCE_UED", ""),
            "password": env.str("PASSWORD_FCE_UED", ""),
            "api_base_url": "https://api.canadiansolar.com",
        },
        "device": {
            "model": "canadian_solar",
            "device_id": env.str("DEVICE_ID_FCE_UED", ""),
        },
        "devices": {
            "FCE_UED": {
                "model": "canadian_solar",
                "device_id": env.str("DEVICE_ID_FCE_UED", ""),
            },
        },
    },
}
