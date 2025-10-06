import warnings
from dataclasses import dataclass, field

warnings.filterwarnings("ignore")


@dataclass
class PVConstants:
    """Physical constants for PV system calculations according to ABNT NBR 16274:2014."""

    STC_IRRADIANCE: float = 1000.0  # W/m²
    STC_TEMPERATURE: float = 25.0  # °C
    NOCT_REFERENCE_IRRAD: float = 800.0  # W/m²
    NOCT_REFERENCE_TEMP: float = 20.0  # °C
    MIN_IRRADIANCE: float = 10.0  # W/m²
    MAX_POWER_FACTOR: float = 1.1  # 110% of capacity


class InverterCoefficients:
    """
    Coeficientes da curva de eficiência do inversor conforme Anexo E (Equação E.2/E.4 NBR 16274).
    Baseados no Canadian Solar CSI-30K-T400GL02-E do PV*SOL
    """

    # Valores iniciais (baseados nas curvas reais dos datasheets)
    k0: float = 0.015  # perdas fixas (~1 a 2%)
    k1: float = 0.045  # perdas proporcionais
    k2: float = 0.050  # perdas quadráticas (curvatura)

    # Intervalos de busca coerentes
    k0_min: float = 0.005  # inversor com autoconsumo baixíssimo
    k0_max: float = 0.025  # perdas fixas maiores (equipamentos menos eficientes)

    k1_min: float = 0.020  # eficiência sobe rápido desde baixas cargas
    k1_max: float = 0.060  # subida menos acentuada / maior dispersão

    k2_min: float = 0.010  # quase linear sem muita curvatura
    k2_max: float = 0.080  # perdas crescentes em carga nominal (mais curvatura)

    # Outros parâmetros de projeto
    total_inverter_power: float = 125.0  # kW (75 + 50)
    max_efficiency: float = 0.987  # 98,7% pico (datasheet)
    min_efficiency: float = 0.80  # 80% mínimo em baixíssima carga
    nominal_efficiency: float = 0.95  # ~95% em carga nominal

    voltage_loss_factor: float = 0.990  # ~1% perdas internas DC
    mppt_loss_factor: float = 0.995  # ~0,5% perdas MPPT


@dataclass
class DCLossCoefficients:
    a0: float = 0.075  # Perdas fixas base (cabeamento, conexões, sujeira)
    a1: float = -0.08  # Melhoria com irradiância
    a2: float = 0.20  # Perdas em alta irradiância

    a0_min: float = 0.005  # 0.5%
    a1_min: float = -0.25  # -25%
    a2_min: float = 0.15  # 15%

    a0_max: float = 0.15  # 15%
    a1_max: float = 0.02  # 2%
    a2_max: float = 0.45  # 45%


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
class ACLossCoefficients:
    """Coeficientes de perdas AC conforme NBR 16274 e dados PV*SOL."""

    wiring: float = 0.015  # 1.5% cabeamento AC
    transformer: float = 0.003  # 0.3% transformador (se houver)
    protection: float = 0.003  # 0.3% proteções (disjuntores, DPS)
    monitoring: float = 0.002  # 0.2% medição/monitoramento
    other: float = 0.003  # 0.3% outras perdas

    ac_loss: float = field(init=False)  # Default calculated field (2.5% total)
    ac_loss_min: float = 0.010  # 1% sistemas premium
    ac_loss_max: float = 0.050  # 5% sistemas com perdas elevadas

    def __post_init__(self):
        self.ac_loss = self.wiring + self.transformer + self.protection + self.monitoring + self.other

        if self.ac_loss < self.ac_loss_min:
            raise ValueError(f"Total AC losses ({self.ac_loss:.3f}) below minimum ({self.ac_loss_min:.3f})")

        if self.ac_loss > self.ac_loss_max:
            raise ValueError(f"Total AC losses ({self.ac_loss:.3f}) above maximum ({self.ac_loss_max:.3f})")


@dataclass
class PVSystemParameters:
    """Parameters for PV system calculations following ABNT NBR 16274:2014 standards."""

    capacity_kwp: float = 125.0
    noct: float = 42.0
    temp_coeff: float = -0.0037
    irrad_coeff: float = 0.031
    inverter_coeffs: InverterCoefficients = field(default_factory=InverterCoefficients)
    constants: PVConstants = field(default_factory=PVConstants)
    optimization_bounds: OptimizationBounds = field(default_factory=OptimizationBounds)
    dc_loss_coeffs: DCLossCoefficients = field(default_factory=DCLossCoefficients)
    ac_loss_coeffs: ACLossCoefficients = field(default_factory=ACLossCoefficients)
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


def create_system_parameters(
    capacity_kwp,
    noct,
    temp_coeff,
    irrad_coeff,
    dc_loss_coeffs,
    inverter_coeffs,
    ac_loss_coeffs=None,
):
    dc_loss_coeffs = DCLossCoefficients(a0=dc_loss_coeffs[0], a1=dc_loss_coeffs[1], a2=dc_loss_coeffs[2])

    inverter_coeffs_obj = InverterCoefficients(
        k0=inverter_coeffs[0],
        k1=inverter_coeffs[1],
        k2=inverter_coeffs[2],
        total_inverter_power=capacity_kwp,
    )

    if ac_loss_coeffs:
        ac_loss_coeffs = ACLossCoefficients(
            wiring=ac_loss_coeffs[0],
            transformer=ac_loss_coeffs[1],
            protection=ac_loss_coeffs[2],
            monitoring=ac_loss_coeffs[3],
            other=ac_loss_coeffs[4],
        )
    else:
        ac_loss_coeffs = ACLossCoefficients(
            wiring=0.0,
            transformer=0.0,
            protection=0.0,
            monitoring=0.0,
            other=0.0,
        )

    return PVSystemParameters(
        capacity_kwp=capacity_kwp,
        noct=noct,
        temp_coeff=temp_coeff,
        irrad_coeff=irrad_coeff,
        dc_loss_coeffs=dc_loss_coeffs,
        inverter_coeffs=inverter_coeffs_obj,
        ac_loss_coeffs=ac_loss_coeffs,
    )
