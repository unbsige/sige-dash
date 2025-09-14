import numpy as np

from src.pages.physical_model.params import PVSystemParameters


class PhysicalPVModel:
    """Baseline physics-based model for PV power prediction using NBR 16274 equations."""

    def __init__(self, params: PVSystemParameters):
        if not isinstance(params, PVSystemParameters):
            raise TypeError("params must be an instance of PVSystemParameters")

        self.capacity_kwp = params.capacity_kwp
        self.noct = params.noct
        self.temp_coeff = params.temp_coeff
        self.irrad_coeff = params.irrad_coeff
        self.inverter_coeffs = params.inverter_coeffs
        self.constants = params.constants
        self.system_config = params.system_config
        self.optimization_bounds = params.optimization_bounds
        self.pvsol_losses = params.pvsol_losses
        self.observed_losses = params.observed_losses
        self.STC_TEMPERATURE = params.constants.STC_TEMPERATURE
        self.STC_IRRADIANCE = params.constants.STC_IRRADIANCE
        self.NOCT_REFERENCE_TEMP = params.constants.NOCT_REFERENCE_TEMP
        self.NOCT_REFERENCE_IRRAD = params.constants.NOCT_REFERENCE_IRRAD

    def calculate_ac_power(self, df, coeffs, irrad_col="gti", air_temp_col="air_temp"):
        """Calculate estimated AC power output for a DataFrame and add intermediate results as new columns.

        Args:
            df: DataFrame with timestamp index, irradiance and air temperature columns
            coeffs: dict with keys 'a0', 'a1', 'a2'
            irrad_col: column name for irradiance (default 'gti')
            air_temp_col: column name for air temperature (default 'air_temp')

        Returns:
            DataFrame copy with new columns:
                - cell_temp
                - dc_power
                - dc_loss_factor
                - dc_adjusted
                - inv_efficiency
                - ac_power_kw_est
        """
        df_out = df.copy()
        self._validate_inputs(df_out, coeffs, irrad_col, air_temp_col)

        df_out["cell_temp"] = self._calculate_cell_temperature(df_out[irrad_col], df_out[air_temp_col])
        df_out["dc_power_kw"] = self._calculate_dc_power(df_out[irrad_col], df_out["cell_temp"])

        df_out["cpdc"] = self._calculate_dc_loss_factor(df_out[irrad_col], coeffs)
        df_out["dc_power_adj_kw"] = df_out["dc_power_kw"] * df_out["cpdc"]
        df_out["inv_efficiency"] = self._calculate_inverter_efficiency(df_out["dc_power_adj_kw"])
        # df_out["inv_efficiency"] = self._calculate_inverter_efficiency_nbr(df_out["dc_power_adj_kw"])

        ac_loss_factor = 1 - self.system_config.ac_loss_factor
        df_out["ac_power_kw_est"] = df_out["dc_power_adj_kw"] * df_out["inv_efficiency"] * ac_loss_factor

        return df_out

    def _calculate_cell_temperature(self, irradiance_wm2, air_temp):
        """Calculate cell temperature using Equation G.1 NBR 16274."""
        return air_temp + (irradiance_wm2 / self.NOCT_REFERENCE_IRRAD) * (self.noct - self.NOCT_REFERENCE_TEMP)

    def _calculate_dc_power(self, irradiance_wm2, cell_temp):
        """Calculate theoretical DC power using Equation E.1 NBR 16274."""
        g_ratio = irradiance_wm2 / self.STC_IRRADIANCE
        temp_factor = 1 + self.temp_coeff * (cell_temp - self.STC_TEMPERATURE)
        irr_factor = 1 + self.irrad_coeff * np.log(np.maximum(g_ratio, 0.01))
        power_dc = self.capacity_kwp * g_ratio * temp_factor * irr_factor
        return power_dc.clip(lower=0, upper=self.capacity_kwp * 1.1)

    def _calculate_dc_loss_factor(self, irradiance_wm2, coeffs):
        """Calculate DC loss factor using Equation F.1 NBR 16274."""
        a0, a1, a2 = coeffs["a0"], coeffs["a1"], coeffs["a2"]
        g_norm = irradiance_wm2 / self.STC_IRRADIANCE

        denominator = g_norm + a0 + a1 * g_norm + a2 * g_norm**2
        denominator = np.clip(denominator, 0.001, None)
        return g_norm / denominator

    def _calculate_inverter_efficiency(self, dc_power_kw):
        """Calculate inverter efficiency based on system configuration."""
        n75_kw = self.system_config.csi_75k_power_kw
        n50_kw = self.system_config.csi_50k_power_kw
        n75_kw_eff = self.system_config.csi_75k_efficiency
        n50_kw_eff = self.system_config.csi_50k_efficiency
        total_inv_power = n75_kw + n50_kw

        eta_nominal = (n75_kw_eff * n75_kw + n50_kw_eff * n50_kw) / total_inv_power
        load_ratio = np.clip(dc_power_kw / total_inv_power, 0, 1.2)

        conditions = [
            load_ratio < 0.02,
            (load_ratio >= 0.02) & (load_ratio < 0.1),
            (load_ratio >= 0.1) & (load_ratio < 0.9),
            load_ratio >= 0.9,
        ]

        choices = [
            eta_nominal * 0.7,
            eta_nominal * (0.7 + 0.25 * (load_ratio - 0.02) / 0.08),
            eta_nominal * 0.99,
            eta_nominal * (1.0 - 0.1 * (load_ratio - 0.9)),
        ]

        efficiency = np.select(conditions, choices, default=eta_nominal * 0.99)
        return np.clip(efficiency, 0, eta_nominal)

    def _calculate_inverter_efficiency_nbr(self, dc_power_kw):
        """Calculate inverter efficiency using NBR 16274 Equation E.2."""
        P_NI = self.system_config.total_inverter_power
        k0, k1, k2 = self.inverter_coeffs.k0, self.inverter_coeffs.k1, self.inverter_coeffs.k2

        load_ratio = dc_power_kw / P_NI
        load_ratio = np.clip(load_ratio, 0.001, 1.2)

        discriminant = (k1 + 1) ** 2 - 4 * k2 * (k0 - load_ratio)
        discriminant = np.maximum(discriminant, 0)

        efficiency = (-(k1 + 1) + np.sqrt(discriminant)) / (2 * k2 * load_ratio)
        efficiency = np.clip(efficiency, 0, 1.0)

        return efficiency

    def _validate_inputs(self, df, coeffs, irrad_col, air_temp_col):
        """Validate inputs for AC power calculation."""
        if df.empty:
            raise ValueError("DataFrame cannot be empty")

        required_cols = [irrad_col, air_temp_col]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        required_coeffs = ["a0", "a1", "a2"]
        missing_coeffs = [c for c in required_coeffs if c not in coeffs]
        if missing_coeffs:
            raise ValueError(f"Missing required coefficients: {missing_coeffs}")

        irradiance = df[irrad_col]
        air_temp = df[air_temp_col]

        if (irradiance < 0).any():
            raise ValueError("Irradiance cannot be negative")

        if (irradiance > 1500).any():
            raise ValueError("Irradiance exceeds physical limits (>1500 W/m²)")

        if (air_temp < -50).any() or (air_temp > 70).any():
            raise ValueError("Air temperature outside reasonable range (-50°C to 70°C)")
