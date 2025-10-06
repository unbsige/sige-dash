import warnings

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, ClassifierMixin, RegressorMixin
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.utils.validation import check_X_y, check_array

from models.physical.coefficients import CoefficientEstimator, PVCoefficientOptimizer
from models.physical.evaluator import PVModelPerformanceEvaluator
from models.physical.params import PVSystemParameters, create_system_parameters
from models.physical.pv_model import PVBaselineModel

warnings.filterwarnings("ignore")


class PVPhysicsEstimator(BaseEstimator, RegressorMixin):
    """Sklearn-compatible wrapper para o modelo físico PV."""

    def __init__(
        self,
        capacity_kwp=125.0,
        noct=42.0,
        temp_coeff=-0.0037,
        irrad_coeff=0.031,
        a0=0.015,
        a1=-0.12,
        a2=0.28,
        k0=-0.0162,
        k1=0.0130,
        k2=-0.0048,
        apply_ac_loss=True,
        apply_dc_loss=True,
        use_nbr_eff=False,
        optimize_coefficients=True,
        optimization_method="L-BFGS-B",
    ):
        self.capacity_kwp = capacity_kwp
        self.noct = noct
        self.temp_coeff = temp_coeff
        self.irrad_coeff = irrad_coeff

        self.a0 = a0
        self.a1 = a1
        self.a2 = a2

        self.k0 = k0
        self.k1 = k1
        self.k2 = k2

        self.apply_ac_loss = apply_ac_loss
        self.apply_dc_loss = apply_dc_loss
        self.use_nbr_eff = use_nbr_eff
        self.optimize_coefficients = optimize_coefficients
        self.optimization_method = optimization_method

        self.pv_model_ = None
        self.optimized_coeffs_ = None
        self.optimization_result_ = None
        self.is_fitted_ = False

        self.feature_names_ = ["gti", "air_temp"]  # irradiância e temperatura do ar
        self.irrad_col_ = "gti"
        self.air_temp_col_ = "air_temp"

    def fit(self, x, y):
        """
        Treina o modelo físico PV.

        Args:
            X: array-like de shape (n_samples, 2) com [irradiância, temperatura_ar]
            y: array-like de shape (n_samples,) com potência AC medida
        """
        x, y = check_X_y(x, y)

        df = self._convert_to_dataframe(x, y)

        dc_coeffs = [self.a0, self.a1, self.a2]
        inverter_coeffs = [self.k0, self.k1, self.k2]

        params = create_system_parameters(
            capacity_kwp=self.capacity_kwp,
            noct=self.noct,
            temp_coeff=self.temp_coeff,
            irrad_coeff=self.irrad_coeff,
            dc_coeffs=dc_coeffs,
            inverter_coeffs=inverter_coeffs,
        )

        self.pv_model_ = PVBaselineModel(
            params=params,
            apply_ac_loss=self.apply_ac_loss,
            apply_dc_loss=self.apply_dc_loss,
            use_nbr_eff=self.use_nbr_eff,
        )

        if self.optimize_coefficients:
            self._optimize_coefficients(df)
        else:
            self.optimized_coeffs_ = {"a0": self.a0, "a1": self.a1, "a2": self.a2}

        self.is_fitted_ = True
        return self

    def predict(self, x):
        """
        Prediz potência AC usando o modelo físico.

        Args:
            X: array-like de shape (n_samples, 2) com [irradiância, temperatura_ar]

        Returns:
            array de shape (n_samples,) com predições de potência AC
        """

        if not self.is_fitted_:
            raise ValueError("Modelo não foi treinado ainda. Chame .fit() primeiro.")

        x = check_array(x)
        df = self._convert_to_dataframe(x)

        df_pred = self.pv_model_.calculate_ac_power(
            df,
            coeffs=self.optimized_coeffs_,
            irrad_col=self.irrad_col_,
            air_temp_col=self.air_temp_col_,
        )

        return df_pred["ac_power_kw_est"].values

    def _convert_to_dataframe(self, x, y=None):
        """Converte array numpy para DataFrame com nomes apropriados."""
        df = pd.DataFrame(x, columns=self.feature_names_)

        if y is not None:
            df["ac_power_measured"] = y

        return df

    def _optimize_coefficients(self, df):
        try:
            pv_losses = {
                "soiling": 0.02,
                "shading": 0.01,
                "mismatch_module": 0.02,
                "dc_wiring": 0.015,
                "low_irradiance": 0.03,
                "temperature": 0.05,
            }

            estimator = CoefficientEstimator(pv_losses)
            initial_coeffs = estimator.estimate_initial_coefficients()

            optimizer = PVCoefficientOptimizer(
                pv_model=self.pv_model_,
                params=self.pv_model_,
                irrad_col=self.irrad_col_,
                air_temp_col=self.air_temp_col_,
                power_col="ac_power_measured",
            )

            result = optimizer.calibrate_with_ac_data(
                df=df, initial_coeffs=initial_coeffs, method=self.optimization_method
            )

            if result["success"]:
                self.optimized_coeffs_ = result["optimized_coeffs"]
                self.optimization_result_ = result
            else:
                # Fallback para coeficientes iniciais se otimização falhar
                self.optimized_coeffs_ = {"a0": self.a0, "a1": self.a1, "a2": self.a2}
                print(f"Otimização falhou: {result.get('message', 'Erro desconhecido')}")

        except Exception as e:
            print(f"Erro na otimização: {e}")
            self.optimized_coeffs_ = {"a0": self.a0, "a1": self.a1, "a2": self.a2}
