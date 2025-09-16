from pathlib import Path

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from rich.console import Console
from rich.table import Table
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, root_mean_squared_error


# MAPE
def mean_absolute_percentage_error(y_true, y_pred):
    y_true, y_pred = np.array(y_true).flatten(), np.array(y_pred).flatten()
    if y_true.shape != y_pred.shape:
        raise ValueError(f"y_true e y_pred devem ter o mesmo tamanho: {y_true.shape} != {y_pred.shape}")

    mask = y_true != 0
    if not np.any(mask):
        print("Aviso: Todos os valores de y_true são zero. MAPE não pode ser calculado.")
        return np.nan

    return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100


# sMAPE
def symmetric_mean_absolute_percentage_error(y_true, y_pred):
    y_true, y_pred = np.array(y_true).flatten(), np.array(y_pred).flatten()

    denominator = np.abs(y_pred) + np.abs(y_true)
    mask = denominator != 0

    if not np.any(mask):
        print("Aviso: Denominador zero em todos os pontos. sMAPE não pode ser calculado.")
        return np.nan

    return np.mean(2 * np.abs(y_pred[mask] - y_true[mask]) / denominator[mask]) * 100


# nMAE (Normalized Mean Absolute Error)
def normalized_mean_absolute_error(y_true, y_pred):
    """Calculate the Normalized Mean Absolute Error (nMAE) between true and predicted values.

    The nMAE is computed as the mean absolute error (MAE) divided by the mean of the true values,
    expressed as a percentage. This metric provides a normalized measure of prediction error,
    making it easier to compare across datasets with different scales.

    Parameters
        y_true (array-like or pd.Series): Ground truth (correct) target values.
        y_pred (array-like or pd.Series): Estimated target values.

    Returns
    float
        The normalized mean absolute error (nMAE) as a percentage. Returns np.nan if the mean of y_true is zero.

    Interpretation of ranges:
        - nMAE ≈ 0%        : Excellent prediction accuracy.
        - 0%   < nMAE ≤ 10%: Very good prediction.
        - 10%  < nMAE ≤ 20%: Good prediction.
        - 20%  < nMAE ≤ 50%: Moderate prediction.
        - nMAE > 50%       : Poor prediction accuracy.
    """

    y_true, y_pred = np.array(y_true).flatten(), np.array(y_pred).flatten()
    mae = mean_absolute_error(y_true, y_pred)
    mean_true = np.mean(y_true)

    if mean_true == 0:
        print("Aviso: Média de y_true é zero. nMAE não pode ser calculado.")
        return np.nan

    return (mae / mean_true) * 100


# nRMSE (Normalized Root Mean Square Error)
def normalized_root_mean_square_error(y_true, y_pred):
    y_true, y_pred = np.array(y_true).flatten(), np.array(y_pred).flatten()
    rmse = root_mean_squared_error(y_true, y_pred)
    mean_true = np.mean(y_true)

    if mean_true == 0:
        print("Aviso: Média de y_true é zero. nRMSE não pode ser calculado.")
        return np.nan

    return (rmse / mean_true) * 100


# Normalized Bias Error (NBE)
def normalized_bias_error(y_true, y_pred):
    """Calculates the Normalized Bias Error (NBE) between true and predicted values.

    The NBE quantifies the systematic tendency of a model to overestimate or underestimate
    the target variable. It is expressed as a percentage of the mean of the true values.
    A positive bias indicates overestimation, while a negative bias indicates underestimation.

    Parameters:
        y_true (array-like): Ground truth (correct) target values.
        y_pred (array-like): Estimated target values.

    Returns:
        float: Normalized bias error as a percentage.

    Interpretation of NBE ranges:
        - 0%: Perfectly unbiased predictions.
        - 0% < NBE <= 5%: Excellent accuracy, minimal bias.
        - 5% < NBE <= 10%: Good accuracy, low bias.
        - 10% < NBE <= 20%: Moderate bias, may require model improvement.
        - NBE > 20%: High bias, model likely unsuitable for reliable predictions.

    Note:
        The sign of the bias (before applying abs) indicates the direction of the bias:
        positive for overestimation, negative for underestimation.

    Detecta se modelo super/subestima sistematicamente.
    Crítico para planejamento de operação.
    """
    bias = np.mean(y_pred - y_true)
    return abs(bias / np.mean(y_true)) * 100


def energy_yield_accuracy(y_true, y_pred):
    """Calculates the accuracy of energy yield predictions over a given period, expressed as a percentage.

    Accuracy ranges interpretation:
        - 90% - 100%: Excellent prediction accuracy
        - 80% - 90%: Good prediction accuracy
        - 70% - 80%: Moderate prediction accuracy
        - Below 70%: Low prediction accuracy; model improvement recommended

    Args:
        y_true (array-like or pd.Series): Actual energy yield values.
        y_pred (array-like or pd.Series): Predicted energy yield values.

    Returns:
        float: Accuracy of the energy yield prediction as a percentage. Returns np.nan if actual yield is zero.
    """

    y_true, y_pred = np.array(y_true).flatten(), np.array(y_pred).flatten()
    if y_true.shape != y_pred.shape:
        raise ValueError(f"y_true and y_pred must have the same shape: {y_true.shape} != {y_pred.shape}")

    actual_yield = np.sum(y_true)
    predicted_yield = np.sum(y_pred)
    if actual_yield == 0:
        print("Warning: Actual yield is zero. Cannot calculate accuracy.")
        return np.nan

    return (1 - abs(actual_yield - predicted_yield) / actual_yield) * 100


def skill_score_daily(y_true, y_pred):
    """
    Persistence model: today = yesterday
    Skill > 0.2 indicates ML is significantly better
    """
    y_true, y_pred = np.array(y_true).flatten(), np.array(y_pred).flatten()
    y_persistence = np.roll(y_true, 1)[1:]  # Shift by one day
    y_true_comp = y_true[1:]
    y_pred_comp = y_pred[1:]

    mse_model = mean_squared_error(y_true_comp, y_pred_comp)
    mse_persistence = mean_squared_error(y_true_comp, y_persistence)

    return 1 - (mse_model / mse_persistence)


def performance_by_sky_conditions(y_true, y_pred, csi=None, ghi=None, clearsky_ghi=None):
    """
    Analyzes performance by sky conditions using the clear sky index (CSI).
    CSI = ghi / ghi_clearsky
    """

    if csi is None:
        if ghi is None or clearsky_ghi is None:
            raise ValueError("If csi is not provided, ghi and clearsky_ghi must be provided.")
        csi = ghi / clearsky_ghi

    clear_days = csi > 0.7  # Clear days
    cloudy_days = csi < 0.4  # Cloudy days
    partial_days = (csi >= 0.4) & (csi <= 0.7)  # Partially cloudy days

    return {
        "nmae_clear": normalized_mean_absolute_error(y_true[clear_days], y_pred[clear_days]),
        "nmae_cloudy": normalized_mean_absolute_error(y_true[cloudy_days], y_pred[cloudy_days]),
        "nmae_partial": normalized_mean_absolute_error(y_true[partial_days], y_pred[partial_days]),
    }


def r2_score_custom(y_true, y_pred):
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    return 1 - (ss_res / ss_tot)


def seasonal_performance(y_true, y_pred, dates):
    """
    Performance por estação do ano
    Detecta se modelo tem viés sazonal
    """
    df = pd.DataFrame({"y_true": y_true, "y_pred": y_pred, "month": pd.to_datetime(dates).month})

    seasons = {
        "summer": [12, 1, 2],  # Brasil
        "autumn": [3, 4, 5],
        "winter": [6, 7, 8],
        "spring": [9, 10, 11],
    }

    results = {}
    for season, months in seasons.items():
        mask = df["month"].isin(months)
        if mask.sum() > 0:
            results[f"nmae_{season}"] = normalized_mean_absolute_error(df.loc[mask, "y_true"], df.loc[mask, "y_pred"])

    return results


def training_efficiency_score(training_time_seconds, performance_score):
    time_penalty = max(0, 1 - (training_time_seconds - 600) / 3600)
    return performance_score * time_penalty


def calculate_forecast_accuracy(y_true, y_pred, y_train=None):
    """Calcula métricas de acurácia para previsões de séries temporais.

    Parâmetros:
        y_true : array-like ou pandas Series (Valores verdadeiros (observados))
        y_pred : array-like ou pandas Series (Valores preditos)
        y_train : pandas Series (Dados de treinamento, opcional)
    """

    return {
        "mae": mean_absolute_error(y_true, y_pred),
        "rmse": root_mean_squared_error(y_true, y_pred),
        "r2": r2_score(y_true, y_pred),
        "mape": mean_absolute_percentage_error(y_true, y_pred),
        "smape": symmetric_mean_absolute_percentage_error(y_true, y_pred),
        "nmae": normalized_mean_absolute_error(y_true, y_pred),
        "nrmse": normalized_root_mean_square_error(y_true, y_pred),
        "nbe": normalized_bias_error(y_true, y_pred),
        "eya": energy_yield_accuracy(y_true, y_pred),
        "skill": skill_score_daily(y_true, y_pred),
    }
    # return pd.DataFrame([metrics])
    # descr = [
    #     "Mean Absolute Error (MAE)",
    #     "Root Mean Squared Error (RMSE)",
    #     "Coefficient of Determination (R²)",
    #     "Mean Absolute Percentage Error (MAPE)",
    #     "Symmetric Mean Absolute Percentage Error (sMAPE)",
    #     "Normalized Mean Absolute Error (nMAE)",
    #     "Normalized Root Mean Squared Error (nRMSE)",
    #     "Normalized Bias Error (NBE)",
    #     "Energy Yield Accuracy (EYA)",
    #     "Skill Score (SS)",
    # ]
    # return pd.DataFrame({
    #     "metric": list(metrics.keys()),
    #     "value": list(metrics.values()),
    #     "description": descr,
    # })


def print_forecast_accuracy(y_true, y_pred, y_train=None, title=""):
    df = calculate_forecast_accuracy(y_true, y_pred, y_train)
    console = Console()
    table = Table(title=f"Resumo das métricas de precisão (forecast accuracy - {title})")
    table.add_column("metric", justify="left")
    table.add_column("value", justify="right")
    table.add_column("description", justify="left")

    for _, row in df.iterrows():
        table.add_row(str(row["metric"]), f"{row['value']:.3f}", str(row["description"]))

    console.print(table)


def save_score_metrics(metrics, name="inter", metadata=None):
    metrics_path = Path.cwd().parent / "data" / "results" / "baseline"
    metrics_path.mkdir(parents=True, exist_ok=True)
    file_path = metrics_path / f"{name}.csv"

    df = metrics.copy() if isinstance(metrics, pd.DataFrame) else pd.DataFrame([metrics])
    df = df.assign(model=name, features=df.index, dataset=metadata.get("dataset", ""))

    columns_order = ["model", "features", "dataset"] + [
        col for col in df.columns if col not in ["model", "features", "dataset"]
    ]
    df = df[columns_order]

    if metadata:
        df = df.assign(**metadata)

    try:
        mode = "a" if file_path.exists() else "w"
        header = not file_path.exists()
        df.to_csv(file_path, mode=mode, header=header, index=False)
        print(f"Métricas salvas com sucesso em: {file_path}")
    except Exception as e:
        print(f"Erro ao salvar as métricas: {e}")


def composite_performance_index(y_true, y_pred, weights=None):
    """
    Combina múltiplas métricas em um índice único
    Útil para ranking automático de modelos
    """

    if weights is None:
        weights = {"nmae": 0.3, "nrmse": 0.3, "mape": 0.2, "skill": 0.2}

    metrics = {
        "nmae": normalized_mean_absolute_error(y_true, y_pred),
        "nrmse": normalized_root_mean_square_error(y_true, y_pred),
        "mape": mean_absolute_percentage_error(y_true, y_pred) / 100,
        "skill": max(0, skill_score_daily(y_true, y_pred)),
    }

    score = (
        weights["nmae"] * metrics["nmae"]
        + weights["nrmse"] * metrics["nrmse"]
        + weights["mape"] * metrics["mape"]
        + weights["skill"] * (1 - metrics["skill"])
    )

    return 1 - score
