from dataclasses import dataclass, field


@dataclass
class InverterCoefficients:
    """Coefficients for inverter efficiency calculations."""

    k0: float = 0.0022
    k1: float = 0.0095
    k2: float = 0.0222


@dataclass
class PVConstants:
    """Physical constants for PV system calculations according to ABNT NBR 16274:2014."""

    STC_IRRADIANCE: float = 1000.0  # W/m²
    STC_TEMPERATURE: float = 25.0  # °C
    NOCT_REFERENCE_IRRAD: float = 800.0  # W/m²
    NOCT_REFERENCE_TEMP: float = 20.0  # °C
    MIN_IRRADIANCE: float = 10.0  # W/m²
    MAX_POWER_FACTOR: float = 1.1  # 110% of capacity


@dataclass
class SystemConfiguration:
    """Configuration for specific PV system setup."""

    csi_75k_efficiency: float = 0.987  # CSI-75K max efficiency
    csi_50k_efficiency: float = 0.988  # CSI-50KTL-GI max efficiency
    csi_75k_power_kw: float = 75.0  # kW
    csi_50k_power_kw: float = 50.0  # kW
    total_inverter_power: float = 125.0  # kW
    ac_loss_factor: float = 0.015  # 1.5% AC losses
    min_load_ratio: float = 0.1  # Minimum load ratio for efficiency


@dataclass
class OptimizationBounds:
    """Bounds for coefficient optimization."""

    a0_min: float = 0.005  # 0.5% minimum fixed losses
    a0_max: float = 0.3  # 30% maximum fixed losses
    a1_min: float = -0.3  # -30% (improves with irradiance)
    a1_max: float = 0.3  # +30% (worsens with irradiance)
    a2_min: float = 0.002  # 0.2% minimum high irradiance losses
    a2_max: float = 0.3  # 30% maximum high irradiance losses


@dataclass
class PVSystemParameters:
    """Parameters for PV system calculations following ABNT NBR 16274:2014 standards."""

    capacity_kwp: float = 125.0
    noct: float = 42.0
    temp_coeff: float = -0.0037
    irrad_coeff: float = 0.031
    inverter_coeffs: InverterCoefficients = field(default_factory=InverterCoefficients)
    constants: PVConstants = field(default_factory=PVConstants)
    system_config: SystemConfiguration = field(default_factory=SystemConfiguration)
    optimization_bounds: OptimizationBounds = field(default_factory=OptimizationBounds)
    pvsol_losses: dict = field(
        default_factory=lambda: {
            "soiling": 0.020,
            "shading": 0.010,
            "temperature": 0.0737,
            "inverter_efficiency": 0.0241,
            "low_irradiance": 0.0299,
            "mismatch_module": 0.020,
            "mismatch_connection": 0.0007,
            "dc_wiring": 0.020,
            "ac_wiring": 0.020,
            "standby_consumption": 0.0001,
        }
    )
    observed_losses: dict = field(
        default_factory=lambda: {
            "soiling": 0.05,
            "equipment_failures": 0.15,
            "string_disconnection": 0.10,
            "dust_accumulation": 0.03,
            "lack_maintenance": 0.08,
            "monitoring_gaps": 0.02,
        }
    )
