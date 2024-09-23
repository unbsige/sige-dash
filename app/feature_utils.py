import numpy as np
import pandas as pd
from config import settings
from sklego.preprocessing import RepeatingBasisFunction


def create_features(df, target, lags=settings.LAGS, windows=settings.WINDOWS):
    df = df.copy()
    df = add_time_features(df)
    df = add_time_since(df)
    df = add_cyclic_features(df)
    df = add_radial_basics_function(df)
    df = add_lagged_features(df, target, lags)
    df = add_window_features(df, target, windows)
    return df


def add_time_since(df):
    time_diff = df.index - df.index.min()
    df["time_since"] = time_diff.total_seconds() / 3600
    df["time_since_2"] = df["time_since"] ** 2
    return df


def add_time_features(df):
    df["hour"] = df.index.hour
    df["day"] = df.index.day
    df["day_of_week"] = df.index.weekday
    df["month"] = df.index.month
    df["is_weekend"] = df.day_of_week.isin([5, 6]).astype(int)
    df["is_night"] = ((df["hour"] >= 18) | (df["hour"] <= 6)).astype(int)
    return df


def add_cyclic_features(df, columns=None, drop_original=False):
    if columns is None:
        columns = ["hour", "day", "day_of_week"]

    for col in columns:
        freq = df[col].max() if df[col].min() != 0 else df[col].max() + 1
        df[f"{col}_sin"] = np.sin(df[col] * (2.0 * np.pi / freq))
        df[f"{col}_cos"] = np.cos(df[col] * (2.0 * np.pi / freq))

    if drop_original:
        df.drop(columns, axis=1, inplace=True)

    return df


def add_radial_basics_function(df):
    rbf = RepeatingBasisFunction(
        n_periods=12,
        column="hour",
        input_range=(0, 23),
        remainder="drop",
    )

    rbf.fit(df)
    df_rbf = pd.DataFrame(
        index=df.index,
        data=rbf.transform(df)
    )

    df_rbf.columns = [f"rbf_{col}" for col in df_rbf.columns if str(col).isdigit()]
    return pd.concat([df, df_rbf], axis=1)


def add_lagged_features(df, col, lags):
    if col not in df.columns:
        raise ValueError(f"Coluna '{col}' não encontrada no DataFrame.")

    if not all(isinstance(lag, int) and lag > 0 for lag in lags):
        raise ValueError("Lags devem ser inteiros positivos.")

    col_lags = []
    for lag in lags:
        column_name = f"lag{lag}"
        df[column_name] = df[col].shift(lag)
        col_lags.append(column_name)

    df["lag_mean"] = df[col_lags].mean(axis="columns")
    df["lag_median"] = df[col_lags].median(axis="columns")
    df["lag_std"] = df[col_lags].std(axis="columns")
    return df


def add_window_features(df, col, windows, aggregations=None):
    if aggregations is None:
        aggregations = ["mean", "median", "std", "min", "max"]

    for window in windows:
        temp = df[col].rolling(window=window).agg(aggregations).shift(1)
        temp.columns = [f"window{window}_{agg}" for agg in aggregations]
        df = pd.concat([df, temp], axis="columns")
    return df
