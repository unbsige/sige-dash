import numpy as np

from src.models.physical.pv_model import PVBaselineModel


class PVModelPerformanceEvaluator:
    """Evaluates photovoltaic model performance through comprehensive statistical metrics."""

    def __init__(self, pv_model: PVBaselineModel):
        self.pv_model = pv_model

    def evaluate_coefficients(self, df, coeffs, irrad_col="gti", air_temp_col="air_temp", power_ac_col="pv_power"):
        """Evaluate the performance of given loss coefficients against measured AC power data.

        Args:
            df: DataFrame containing measurement data.
            coeffs: Dictionary with keys 'a0', 'a1', 'a2' (loss coefficients).
            irrad_col: Column name for irradiance (default: 'gti').
            air_temp_col: Column name for air temperature (default: 'air_temp').
            power_ac_col: Column name for measured AC power (default: 'pv_power').

        Returns:
            Dictionary with validation metrics (MAE, nMAE, RMSE, nRMSE, R², mean bias, etc.).
        """
        df_pred = self.pv_model.calculate_ac_power(df, coeffs, irrad_col=irrad_col, air_temp_col=air_temp_col)
        return self._calculate_metrics(df_pred[power_ac_col], df_pred["ac_power_kw_est"])

    def _calculate_metrics(self, y_true, y_pred):
        """Calculate validation metrics and return summary metrics."""
        return {
            "n_points": len(y_true),
            "mae": np.mean(np.abs(y_true - y_pred)),
            "nmae": self._calculate_nmae(y_true, y_pred),
            "rmse": self._calculate_rmse(y_true, y_pred),
            "nrmse": self._calculate_nrmse(y_true, y_pred),
            "r2_score": self._calculate_r2(y_true, y_pred),
            "mean_bias": np.mean(y_pred - y_true),
        }

    def _calculate_nmae(self, y_true, y_pred):
        mae = np.mean(np.abs(y_true - y_pred))
        mean_measured = np.mean(y_true)
        return 100 * mae / mean_measured if mean_measured != 0 else np.inf

    def _calculate_rmse(self, y_true, y_pred):
        return np.sqrt(np.mean((y_true - y_pred) ** 2))

    def _calculate_nrmse(self, y_true, y_pred):
        rmse = self._calculate_rmse(y_true, y_pred)
        return rmse / np.mean(y_true) if np.any(y_true) else np.nan

    def _calculate_r2(self, y_true, y_pred):
        if len(y_true) <= 1:
            return np.nan
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        return 1 - ss_res / ss_tot if ss_tot != 0 else np.nan
