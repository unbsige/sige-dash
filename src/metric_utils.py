import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


# MAPE
def mean_absolute_percentage_error(y_true, y_pred):
    y_true, y_pred = np.array(y_true).flatten(), np.array(y_pred).flatten()

    if y_true.shape != y_pred.shape:
        raise ValueError(f"y_true e y_pred devem ter o mesmo tamanho: {y_true.shape} != {y_pred.shape}")

    mask = y_true != 0
    return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask]))


# sMAPE
def symmetric_mean_absolute_percentage_error(y_true, y_pred):
    return np.mean(np.abs(y_pred - y_true) / (np.abs(y_pred) + np.abs(y_true)))


# MASE
def mean_absolute_scaled_error(y_true, y_pred, y_train):
    mae_model = mean_absolute_error(y_true, y_pred)

    try:
        hour_median_train = y_train.groupby(y_train.index.hour).median()
        mapped_values = y_true.index.hour.map(hour_median_train)
        mae_naive = mean_absolute_error(y_true, mapped_values)

        return 0 if mae_naive == 0 else mae_model / mae_naive

    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def calculate_forecast_accuracy(y_true, y_pred, y_train):
    y_true_day = y_true.between_time('06:00:00', '18:00:00')
    y_pred_day = y_pred.between_time('06:00:00', '18:00:00')
    y_train_day = y_train.between_time('06:00:00', '18:00:00')

    return {
        "mae": mean_absolute_error(y_true, y_pred),
        "rmse": mean_squared_error(y_true, y_pred, squared=False),
        "mse": mean_squared_error(y_true, y_pred),
        "r2": r2_score(y_true, y_pred),
        "mape": mean_absolute_percentage_error(y_true, y_pred),
        "mase": mean_absolute_scaled_error(y_true, y_pred, y_train),
        
        "mae_day": mean_absolute_error(y_true_day, y_pred_day),
        "rmse_day": mean_squared_error(y_true_day, y_pred_day, squared=False),
        "mse_day": mean_squared_error(y_true_day, y_pred_day),
        "r2_day": r2_score(y_true_day, y_pred_day),
        "mape_day": mean_absolute_percentage_error(y_true_day, y_pred_day),
        "mase_day": mean_absolute_scaled_error(y_true_day, y_pred_day, y_train_day),
    }
