import numpy as np

from src.models.physical.params import PVSystemParameters


class PVBaselineModel:
    """Baseline physics-based model for PV power prediction using NBR 16274 equations."""

    def __init__(
        self,
        params: PVSystemParameters,
        apply_ac_loss=True,
        apply_dc_loss=True,
        use_nbr_eff=False,
        global_correction_factor=1,
    ):
        self.capacity_kwp = params.capacity_kwp
        self.noct = params.noct
        self.temp_coeff = params.temp_coeff
        self.irrad_coeff = params.irrad_coeff
        self.ac_loss_coeff = params.ac_loss_coeffs
        self.dc_loss_coeffs = params.dc_loss_coeffs
        self.inverter_coeffs = params.inverter_coeffs

        self.constants = params.constants
        self.STC_TEMPERATURE = params.constants.STC_TEMPERATURE
        self.STC_IRRADIANCE = params.constants.STC_IRRADIANCE
        self.NOCT_REFERENCE_TEMP = params.constants.NOCT_REFERENCE_TEMP
        self.NOCT_REFERENCE_IRRAD = params.constants.NOCT_REFERENCE_IRRAD

        self.apply_ac_loss = apply_ac_loss
        self.apply_dc_loss = apply_dc_loss
        self.use_nbr_eff = use_nbr_eff
        self.global_correction_factor = global_correction_factor

    def calculate_ac_power(self, df, irrad_col="gti", air_temp_col="air_temp", coeffs=None):
        """
        Calculate estimated AC power output for a DataFrame and add intermediate results as new columns.

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
        if self.apply_dc_loss and coeffs is None:
            coeffs = {
                "a0": self.dc_loss_coeffs.a0,
                "a1": self.dc_loss_coeffs.a1,
                "a2": self.dc_loss_coeffs.a2,
            }

        self._validate_inputs(df_out, coeffs, irrad_col, air_temp_col)

        df_out["cell_temp"] = self._calculate_cell_temperature(df_out[irrad_col], df_out[air_temp_col])
        df_out["dc_power_kw"] = self._calculate_dc_power(df_out[irrad_col], df_out["cell_temp"])

        df_out["cpdc"] = self._calculate_dc_loss_factor(df_out[irrad_col], coeffs) if self.apply_dc_loss else 1.0
        df_out["dc_power_adj_kw"] = df_out["dc_power_kw"] * df_out["cpdc"]

        df_out["inv_efficiency"] = (
            self._calculate_inverter_efficiency_nbr(df_out["dc_power_adj_kw"])
            if self.use_nbr_eff
            else self._calculate_inverter_efficiency(df_out["dc_power_adj_kw"])
        )

        ac_loss_factor = (1 - self.ac_loss_coeff.ac_loss) if self.apply_ac_loss else 1.0
        df_out["ac_power_kw_est"] = df_out["dc_power_adj_kw"] * df_out["inv_efficiency"] * ac_loss_factor

        # Apply global correction factor (NBE = 17.9% losses)
        if self.global_correction_factor != 1:
            global_correction_factor = 1 - 0.179
            df_out["ac_power_kw_est"] *= global_correction_factor

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
        """
        Calculate inverter efficiency based on PV*SOL simulation data.

        Derived from Canadian Solar CSI-30K-T400GL02-E performance data:
        - Conversion DC/AC losses: 2.41%
        - MPPT tracking losses: 0.50%
        - Voltage deviation losses: 0.99%
        """

        total_inv_power = self.inverter_coeffs.total_inverter_power
        voltage_loss_factor = 0.9901  # 99.01%
        mppt_loss_factor = 0.9950  # 99.50%

        load_ratio = np.clip(dc_power_kw / total_inv_power, 0, 1.2)
        load_points = np.array([0.0, 0.05, 0.10, 0.20, 0.50, 0.75, 1.0, 1.1, 1.2])
        eff_points = np.array([0.0, 0.80, 0.91, 0.94, 0.98, 0.97, 0.95, 0.94, 0.92])

        efficiency = np.interp(load_ratio, load_points, eff_points)
        efficiency *= voltage_loss_factor * mppt_loss_factor
        return np.clip(efficiency, 0, 0.99)

    def _calculate_inverter_efficiency_nbr(self, dc_power_kw):
        """Calculate inverter efficiency using NBR 16274 Equation E.2."""

        p_ni = self.inverter_coeffs.total_inverter_power
        k0 = self.inverter_coeffs.k0
        k1 = self.inverter_coeffs.k1
        k2 = self.inverter_coeffs.k2
        min_eff = self.inverter_coeffs.min_efficiency
        max_eff = self.inverter_coeffs.max_efficiency

        load_ratio = dc_power_kw / p_ni
        load_ratio = np.clip(load_ratio, 0.001, 1.2)

        discriminant = (k1 + 1) ** 2 - 4 * k2 * (k0 - load_ratio)
        discriminant = np.maximum(discriminant, 0)

        # efficiency = (-(k1 + 1) + np.sqrt(discriminant)) / (2 * k2 * load_ratio)
        pac_normalized = (-(k1 + 1) + np.sqrt(discriminant)) / (2 * k2)
        efficiency = pac_normalized / load_ratio
        efficiency = np.clip(efficiency, min_eff, max_eff)

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
