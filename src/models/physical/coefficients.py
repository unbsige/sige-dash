import numpy as np
from scipy.optimize import minimize


class CoefficientEstimator:
    """Estimator for initial coefficient values based on PV_SOL simulation data."""

    def __init__(self, pv_losses):
        self.losses = pv_losses

    def estimate_a0(self):
        """Estimate a0 coefficient (fixed losses independent of irradiance)."""
        components = {
            "soiling": self.losses.get("soiling", 0.0),
            "shading": self.losses.get("shading", 0.0),
            "mismatch_module": self.losses.get("mismatch_module", 0.0),
            "dc_wiring_fixed": self.losses.get("dc_wiring", 0.0) * 0.5,
        }
        return sum(components.values()), components

    def estimate_a1(self):
        """Estimate a1 coefficient (MPPT efficiency and low irradiance behavior)."""
        components = {
            "mppt_efficiency": -0.005,
            "low_irradiance_penalty": -self.losses.get("low_irradiance", 0.0) * 2,
            "inverter_startup": -0.01,
        }
        return sum(components.values()), components

    def estimate_a2(self):
        """Estimate a2 coefficient (high irradiance losses)."""
        components = {
            "temperature_saturation": self.losses.get("temperature", 0.0) * 0.4,
            "inverter_saturation": 0.05,
            "high_irr_clipping": 0.02,
        }
        return sum(components.values()), components

    def estimate_initial_coefficients(self):
        """Generate initial coefficient estimates."""
        a0, a0_components = self.estimate_a0()
        a1, a1_components = self.estimate_a1()
        a2, a2_components = self.estimate_a2()

        return {
            "a0": a0,
            "a1": a1,
            "a2": a2,
            "source": "PV_SOL simulation",
            "breakdown": {
                "a0_components": a0_components,
                "a1_components": a1_components,
                "a2_components": a2_components,
            },
        }


class PVCoefficientOptimizer:
    """Classe para otimização de coeficientes do sistema PV."""

    def __init__(self, pv_model, params, irrad_col="gti", air_temp_col="air_temp", power_col="ac_power_kw"):
        self.pv_model = pv_model
        self.params = params
        self.irrad_col = irrad_col
        self.air_temp_col = air_temp_col
        self.power_col = power_col
        self.iteration_count = 0

    def calibrate_with_ac_data(self, df, initial_coeffs, method="L-BFGS-B"):
        """Calibrate loss coefficients using real AC measurement data.

        This method optimizes the loss coefficients (a0, a1, a2) for the PV system model
        by minimizing the error between measured AC power and the model's estimated AC power.

        Args:
            df_base: DataFrame containing measurement data
            power_ac_col: Column name for measured AC power (W)
            irrad_col: Column name for irradiance (W/m²)
            air_temp_col: Column name for air temperature (°C)

        Returns:

        """
        self.iteration_count = 0
        initial_guess = np.array([initial_coeffs["a0"], initial_coeffs["a1"], initial_coeffs["a2"]])
        bounds = self._get_optimization_bounds()

        result = minimize(
            fun=self._objective_function,
            x0=initial_guess,
            args=(df,),
            method=method,
            bounds=bounds,
            options={"maxiter": 500, "ftol": 1e-6, "gtol": 1e-5, "eps": 1e-8},
        )

        if not result.success:
            print("\nOtimização falhou!")
            print(f"Motivo: {result.message}")
            return {"success": False, "message": result.message, "scipy_result": result}

        optimized_coeffs = {
            "a0": round(float(result.x[0]), 4),
            "a1": round(float(result.x[1]), 4),
            "a2": round(float(result.x[2]), 4),
        }

        return {
            "success": True,
            "optimized_coeffs": optimized_coeffs,
            "objective_value": result.fun,
            "iterations": result.nit if hasattr(result, "nit") else None,
            "scipy_result": result,
        }

    def _get_optimization_bounds(self) -> list:
        """Retorna os bounds para otimização."""
        bounds = self.params.optimization_bounds
        return [
            (bounds.a0_min, bounds.a0_max),
            (bounds.a1_min, bounds.a1_max),
            (bounds.a2_min, bounds.a2_max),
        ]

    def _objective_function(self, coeffs_array, df):
        try:
            coeffs = {
                "a0": float(coeffs_array[0]),
                "a1": float(coeffs_array[1]),
                "a2": float(coeffs_array[2]),
            }

            df_pred = self.pv_model.calculate_ac_power(
                df,
                coeffs,
                irrad_col=self.irrad_col,
                air_temp_col=self.air_temp_col,
            )

            nmae = self._calculate_nmae(df_pred[self.power_col], df_pred["ac_power_kw_est"])
            mae = np.mean(np.abs(df_pred[self.power_col] - df_pred["ac_power_kw_est"]))

            self.iteration_count += 1
            if self.iteration_count % 10 == 0:
                self._print_interation_info(self.iteration_count, mae, nmae, coeffs)

            return nmae

        except Exception as e:
            print(f"  Erro na função objetivo: {e}")
            return np.inf

    def _calculate_nmae(self, y_true, y_pred):
        mae = np.mean(np.abs(y_true - y_pred))
        mean_measured = np.mean(y_true)
        return 100 * mae / mean_measured if mean_measured != 0 else np.inf

    def _print_iteration_info(self, iteration, mae, nmae, coeffs):
        coeff_str = f"a0={coeffs['a0']:.4f}, a1={coeffs['a1']:.4f}, a2={coeffs['a2']:.4f}"
        print(f"  Iteração {iteration}: nMAE = {nmae:.2f}% | MAE = {mae:.4f} kW | Coeffs: {coeff_str}")
