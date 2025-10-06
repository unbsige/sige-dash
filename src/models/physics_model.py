import numpy as np
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.utils.validation import check_X_y, check_array

from src.models.base_model import BaseMLModel


class PVPhysicsEstimator(BaseEstimator, RegressorMixin):
    """PV physics model based on NBR 16274."""

    def __init__(self, capacity_kwp=125.0, noct=42.0, temp_coeff=-0.0037, irrad_coeff=0.031, ac_efficiency=0.95):
        self.capacity_kwp = capacity_kwp
        self.noct = noct
        self.temp_coeff = temp_coeff
        self.irrad_coeff = irrad_coeff
        self.ac_efficiency = ac_efficiency

        # Constants from NBR 16274
        self.STC_TEMPERATURE = 25.0
        self.STC_IRRADIANCE = 1000.0
        self.NOCT_REFERENCE_TEMP = 20.0
        self.NOCT_REFERENCE_IRRAD = 800.0

    def fit(self, x, y):
        """Fit method for sklearn compatibility (physics model doesn't need training)."""
        x, y = check_X_y(x, y)

        if x.shape[1] < 2:
            raise ValueError(f"Expected at least 2 features [gti, air_temp], got {x.shape[1]}")

        return self

    def predict(self, x):
        """Predict AC power using NBR 16274 physics equations."""
        x = check_array(x)

        if x.shape[1] < 2:
            raise ValueError(f"Expected at least 2 features [gti, air_temp], got {x.shape[1]}")

        irradiance = x[:, 0]  # W/m²
        air_temp = x[:, 1]  # °C

        # Cell temperature calculation (NBR 16274 Equation G.1)
        cell_temp = air_temp + (irradiance / self.NOCT_REFERENCE_IRRAD) * (self.noct - self.NOCT_REFERENCE_TEMP)

        # DC Power calculation (NBR 16274 Equation E.1)
        g_ratio = irradiance / self.STC_IRRADIANCE
        temp_factor = 1 + self.temp_coeff * (cell_temp - self.STC_TEMPERATURE)
        irr_factor = 1 + self.irrad_coeff * np.log(np.maximum(g_ratio, 0.01))

        dc_power = self.capacity_kwp * g_ratio * temp_factor * irr_factor
        dc_power = np.clip(dc_power, 0, self.capacity_kwp * 1.1)

        # AC conversion
        ac_power = dc_power * self.ac_efficiency

        return np.maximum(ac_power, 0.0)


class PVPhysicsModel(BaseMLModel):
    """PV Physics model wrapper for the playground."""

    def __init__(self):
        super().__init__("PV Physics NBR16274", "physics")

    def create_model(self, **params):
        """Create PV physics model with parameters."""
        self.model = PVPhysicsEstimator(
            capacity_kwp=params.get("capacity_kwp", 125.0),
            noct=params.get("noct", 42.0),
            temp_coeff=params.get("temp_coeff", -0.0037),
            irrad_coeff=params.get("irrad_coeff", 0.031),
            ac_efficiency=params.get("ac_efficiency", 0.95),
        )
        return self.model

    def get_default_params(self):
        """Default parameters for Streamlit UI."""
        return {
            "capacity_kwp": 125.0,
            "noct": 42.0,
            "temp_coeff": -0.0037,
            "irrad_coeff": 0.031,
            "ac_efficiency": 0.95,
        }

    def get_param_ranges(self):
        """Parameter ranges for UI sliders."""
        return {
            "capacity_kwp": {"min": 50.0, "max": 500.0, "step": 5.0},
            "noct": {"min": 35.0, "max": 55.0, "step": 0.5},
            "temp_coeff": {"min": -0.006, "max": -0.002, "step": 0.0001},
            "irrad_coeff": {"min": 0.01, "max": 0.05, "step": 0.001},
            "ac_efficiency": {"min": 0.85, "max": 0.98, "step": 0.01},
        }
