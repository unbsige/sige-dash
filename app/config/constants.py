import pandas as pd

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

EXOG_FEATURES = [
    "air_temp",
    "ghi",
    "dni",
    "dhi",
    "gti",
    "clearsky_dhi",
    "clearsky_ghi",
    "clearsky_gti",
    "clearsky_dni",
    "cloud_opacity"
]

EXOG_FEATURES = [
    "air_temp",
    "ghi",
    "dni",
    "dhi",
    "gti",
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

TE = TIME_FEATURES + EXOG_FEATURES
CE = CYCLIC_FEATURES + EXOG_FEATURES
LE = LAG_FEATURES + EXOG_FEATURES
RE = RADIAL_FEATURES + EXOG_FEATURES
SE = SINCE_FEATURES + EXOG_FEATURES
WE = WINDOWS_FEATURES + EXOG_FEATURES

TCE = TIME_FEATURES + CYCLIC_FEATURES + EXOG_FEATURES
TLE = TIME_FEATURES + LAG_FEATURES + EXOG_FEATURES
TRE = TIME_FEATURES + RADIAL_FEATURES + EXOG_FEATURES
TSE = TIME_FEATURES + SINCE_FEATURES + EXOG_FEATURES
TWE = TIME_FEATURES + WINDOWS_FEATURES + EXOG_FEATURES
CLE = CYCLIC_FEATURES + LAG_FEATURES + EXOG_FEATURES
CRE = CYCLIC_FEATURES + RADIAL_FEATURES + EXOG_FEATURES
CSE = CYCLIC_FEATURES + SINCE_FEATURES + EXOG_FEATURES
CWE = CYCLIC_FEATURES + WINDOWS_FEATURES + EXOG_FEATURES
LRE = LAG_FEATURES + RADIAL_FEATURES + EXOG_FEATURES
LSE = LAG_FEATURES + SINCE_FEATURES + EXOG_FEATURES
LWE = LAG_FEATURES + WINDOWS_FEATURES + EXOG_FEATURES
WRE = WINDOWS_FEATURES + RADIAL_FEATURES + EXOG_FEATURES
WSE = WINDOWS_FEATURES + SINCE_FEATURES + EXOG_FEATURES
SRE = SINCE_FEATURES + RADIAL_FEATURES + EXOG_FEATURES

# Combinações de tres grupos de features + exog_features = C(6, 3) = 20
TCLE = TIME_FEATURES + CYCLIC_FEATURES + LAG_FEATURES + EXOG_FEATURES
TCRE = TIME_FEATURES + CYCLIC_FEATURES + RADIAL_FEATURES + EXOG_FEATURES
TCSE = TIME_FEATURES + CYCLIC_FEATURES + SINCE_FEATURES + EXOG_FEATURES
TCWE = TIME_FEATURES + CYCLIC_FEATURES + WINDOWS_FEATURES + EXOG_FEATURES
TLRE = TIME_FEATURES + LAG_FEATURES + RADIAL_FEATURES + EXOG_FEATURES
TLSE = TIME_FEATURES + LAG_FEATURES + SINCE_FEATURES + EXOG_FEATURES
TLWE = TIME_FEATURES + LAG_FEATURES + WINDOWS_FEATURES + EXOG_FEATURES
TRSE = TIME_FEATURES + RADIAL_FEATURES + SINCE_FEATURES + EXOG_FEATURES
TRWE = TIME_FEATURES + RADIAL_FEATURES + WINDOWS_FEATURES + EXOG_FEATURES
TSWE = TIME_FEATURES + SINCE_FEATURES + WINDOWS_FEATURES + EXOG_FEATURES
CLRE = CYCLIC_FEATURES + LAG_FEATURES + RADIAL_FEATURES + EXOG_FEATURES
CLSE = CYCLIC_FEATURES + LAG_FEATURES + SINCE_FEATURES + EXOG_FEATURES
CLWE = CYCLIC_FEATURES + LAG_FEATURES + WINDOWS_FEATURES + EXOG_FEATURES
CRSE = CYCLIC_FEATURES + RADIAL_FEATURES + SINCE_FEATURES + EXOG_FEATURES
CRWE = CYCLIC_FEATURES + RADIAL_FEATURES + WINDOWS_FEATURES + EXOG_FEATURES
CSWE = CYCLIC_FEATURES + SINCE_FEATURES + WINDOWS_FEATURES + EXOG_FEATURES
LRSE = LAG_FEATURES + RADIAL_FEATURES + SINCE_FEATURES + EXOG_FEATURES
LRWE = LAG_FEATURES + RADIAL_FEATURES + WINDOWS_FEATURES + EXOG_FEATURES
LSWE = LAG_FEATURES + SINCE_FEATURES + WINDOWS_FEATURES + EXOG_FEATURES
RSWE = RADIAL_FEATURES + SINCE_FEATURES + WINDOWS_FEATURES + EXOG_FEATURES


# Combinações de quantro grupos de features + exog_features
TCLRE = TIME_FEATURES + CYCLIC_FEATURES + LAG_FEATURES + RADIAL_FEATURES + EXOG_FEATURES
TCLSE = TIME_FEATURES + CYCLIC_FEATURES + LAG_FEATURES + SINCE_FEATURES + EXOG_FEATURES
TCLWE = TIME_FEATURES + CYCLIC_FEATURES + LAG_FEATURES + WINDOWS_FEATURES + EXOG_FEATURES
TCRSE = TIME_FEATURES + CYCLIC_FEATURES + RADIAL_FEATURES + SINCE_FEATURES + EXOG_FEATURES
TCRWE = TIME_FEATURES + CYCLIC_FEATURES + RADIAL_FEATURES + WINDOWS_FEATURES + EXOG_FEATURES
TCSWE = TIME_FEATURES + CYCLIC_FEATURES + SINCE_FEATURES + WINDOWS_FEATURES + EXOG_FEATURES
TLRSE = TIME_FEATURES + LAG_FEATURES + RADIAL_FEATURES + SINCE_FEATURES + EXOG_FEATURES
TLRWE = TIME_FEATURES + LAG_FEATURES + RADIAL_FEATURES + WINDOWS_FEATURES + EXOG_FEATURES
TLSWE = TIME_FEATURES + LAG_FEATURES + SINCE_FEATURES + WINDOWS_FEATURES + EXOG_FEATURES
TRSWE = TIME_FEATURES + RADIAL_FEATURES + SINCE_FEATURES + WINDOWS_FEATURES + EXOG_FEATURES
CLRSE = CYCLIC_FEATURES + LAG_FEATURES + RADIAL_FEATURES + SINCE_FEATURES + EXOG_FEATURES
CLRWE = CYCLIC_FEATURES + LAG_FEATURES + RADIAL_FEATURES + WINDOWS_FEATURES + EXOG_FEATURES
CLSWE = CYCLIC_FEATURES + LAG_FEATURES + SINCE_FEATURES + WINDOWS_FEATURES + EXOG_FEATURES
CRSWE = CYCLIC_FEATURES + RADIAL_FEATURES + SINCE_FEATURES + WINDOWS_FEATURES + EXOG_FEATURES
LRSWE = LAG_FEATURES + RADIAL_FEATURES + SINCE_FEATURES + WINDOWS_FEATURES + EXOG_FEATURES


# Combinações de cinco grupos de features + exog_features = C(6, 5) = 6
TCLRSE = TIME_FEATURES + CYCLIC_FEATURES + LAG_FEATURES + RADIAL_FEATURES + SINCE_FEATURES + EXOG_FEATURES
TCLRWE = TIME_FEATURES + CYCLIC_FEATURES + LAG_FEATURES + RADIAL_FEATURES + WINDOWS_FEATURES + EXOG_FEATURES
TCLSWE = TIME_FEATURES + CYCLIC_FEATURES + LAG_FEATURES + SINCE_FEATURES + WINDOWS_FEATURES + EXOG_FEATURES
TCRSWE = TIME_FEATURES + CYCLIC_FEATURES + RADIAL_FEATURES + SINCE_FEATURES + WINDOWS_FEATURES + EXOG_FEATURES
TLRSWE = TIME_FEATURES + LAG_FEATURES + RADIAL_FEATURES + SINCE_FEATURES + WINDOWS_FEATURES + EXOG_FEATURES
CLRSWE = CYCLIC_FEATURES + LAG_FEATURES + RADIAL_FEATURES + SINCE_FEATURES + WINDOWS_FEATURES + EXOG_FEATURES

# Todas as features combinadas = C(6, 6) = 1
FEATURES_ALL = (
    TIME_FEATURES + CYCLIC_FEATURES + LAG_FEATURES + RADIAL_FEATURES + SINCE_FEATURES + WINDOWS_FEATURES + EXOG_FEATURES
)


feature_sets = {
    "EF": EXOG_FEATURES,
    "TE" : TE,
    "CE" : CE,
    "LE" : LE,
    "RE" : RE,
    "SE" : SE,
    "WE" : WE,
    "TCE" : TCE,
    "TLE" : TLE,
    "TRE" : TRE,
    "TSE" : TSE,
    "TWE" : TWE,
    "CLE" : CLE,
    "CRE" : CRE,
    "CSE" : CSE,
    "CWE" : CWE,
    "LRE" : LRE,
    "LSE" : LSE,
    "LWE" : LWE,
    "WRE" : WRE,
    "WSE" : WSE,
    "SRE" : SRE,
    "TCLE" : TCLE,
    "TCRE" : TCRE,
    "TCSE" : TCSE,
    "TCWE" : TCWE,
    "TLRE" : TLRE,
    "TLSE" : TLSE,
    "TLWE" : TLWE,
    "TRSE" : TRSE,
    "TRWE" : TRWE,
    "TSWE" : TSWE,
    "CLRE" : CLRE,
    "CLSE" : CLSE,
    "CLWE" : CLWE,
    "CRSE" : CRSE,
    "CRWE" : CRWE,
    "CSWE" : CSWE,
    "LRSE" : LRSE,
    "LRWE" : LRWE,
    "LSWE" : LSWE,
    "RSWE" : RSWE,
    "TCLRE" : TCLRE,
    "TCLSE" : TCLSE,
    "TCLWE" : TCLWE,
    "TCRSE" : TCRSE,
    "TCRWE" : TCRWE,
    "TCSWE" : TCSWE,
    "TLRSE" : TLRSE,
    "TLRWE" : TLRWE,
    "TLSWE" : TLSWE,
    "TRSWE" : TRSWE,
    "CLRSE" : CLRSE,
    "CLRWE" : CLRWE,
    "CLSWE" : CLSWE,
    "CRSWE" : CRSWE,
    "LRSWE" : LRSWE,
    "TCLRSE" : TCLRSE,
    "TCLRWE" : TCLRWE,
    "TCLSWE" : TCLSWE,
    "TCRSWE" : TCRSWE,
    "TLRSWE" : TLRSWE,
    "CLRSWE" : CLRSWE,
    "ALL": FEATURES_ALL,
}
