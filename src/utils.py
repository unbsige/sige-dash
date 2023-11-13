import pickle
from pathlib import Path

import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


# MAPE
def mean_absolute_percentage_error(y_true, y_pred):
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    return (
        np.mean(
            np.abs((y_true[y_true != 0] - y_pred[y_true != 0]) / y_true[y_true != 0])
        )
        * 100
    )


# sMAPE
def symmetric_mean_absolute_percentage_error(y_true, y_pred):
    return 200 * np.mean(np.abs(y_pred - y_true) / (np.abs(y_pred) + np.abs(y_true)))


# MASE
def scaled_mean_absolute_error(y_true, y_pred, y_train):
    n = y_train.shape[0]
    d = np.abs(np.diff(y_train)).sum() / (n - 1)
    errors = np.abs(y_pred - y_true)
    return errors.mean() / d


# RMSE
def root_mean_squared_error(y_true, y_pred):
    return np.sqrt(mean_squared_error(y_true, y_pred))


def print_forecast_accuracy(y_true, y_pred, title):
    acc = calculate_forecast_accuracy(y_true, y_pred)

    print("\n" + "=" * 120)
    print(f"Resumo das métricas de precisão ({title})".center(120))
    print("=" * 120 + "\n")

    print(f"MAE: {acc['mae']:>8.2f} - Média da diferença entre previsões e valores reais.")
    print(f"RMSE: {acc['rmse']:>8.2f} - Erro médio do modelo em relação aos valores observados.")
    print(f"R²: {acc['r2']:>8.2f} - Coeficiente de determinação R².")
    print(f"MSE: {acc['mse']:>8.2f} - Média dos quadrados das diferenças entre previstos e reais.")
    print(f"MAPE: {acc['mape']:>7.2f}% - Desvio percentual médio das previsões em relação aos valores reais.")
    print(f"sMAPE: {acc['smape']:>7.2f}% - Indica desvio percentual médio das previsões.")
    print("=" * 120 + "\n")


def calculate_forecast_accuracy(y_true, y_pred):
    return {
        "mae": mean_absolute_error(y_true, y_pred),
        "rmse": root_mean_squared_error(y_true, y_pred),
        "mse": mean_squared_error(y_true, y_pred),
        "r2": r2_score(y_true, y_pred),
        "mape": mean_absolute_percentage_error(y_true, y_pred),
        "smape": symmetric_mean_absolute_percentage_error(y_true, y_pred),
    }


def save_model(model):
    try:
        model_path = Path("modelo/extra_tree_model.joblib")
        with model_path.open(mode="wb") as file:
            pickle.dump(model, file)
    except Exception:
        Path("modelo").mkdir(parents=True, exist_ok=True)
        model_path = Path("modelo/extra_tree_model.joblib")
        with model_path.open(mode="wb") as file:
            pickle.dump(model, file)
