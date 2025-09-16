import warnings
from dataclasses import dataclass, field
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

warnings.filterwarnings("ignore")


@dataclass
class PVConstants:
    """Constantes físicas para cálculos PV conforme ABNT NBR 16274:2014."""

    STC_IRRADIANCE: float = 1000.0  # W/m² - Condições padrão de ensaio
    STC_TEMPERATURE: float = 25.0  # °C - Condições padrão de ensaio
    NOCT_REFERENCE_IRRAD: float = 800.0  # W/m² - Irradiância de referência para NOCT
    NOCT_REFERENCE_TEMP: float = 20.0  # °C - Temperatura ambiente de referência para NOCT
    MIN_IRRADIANCE: float = 10.0  # W/m²
    MAX_POWER_FACTOR: float = 1.1  # 110% da capacidade


@dataclass
class InverterCoefficients:
    """
    Coeficientes da curva de eficiência do inversor conforme Anexo E (Equação E.2/E.4 NBR 16274).
    Baseados no Canadian Solar CSI-30K-T400GL02-E do PV*SOL
    """

    k0: float = -0.0162  # Termo constante
    k1: float = 0.0130  # Termo linear
    k2: float = -0.0048  # Termo quadrático

    k0_min: float = -0.0300  # Inversores menos eficientes
    k1_min: float = 0.0080  # Melhor linearidade
    k2_min: float = -0.0080  # Menos perdas em carga alta

    k0_max: float = -0.0080  # Inversores premium
    k1_max: float = 0.0250  # Pior linearidade
    k2_max: float = -0.0020  # Mais perdas em carga alta

    inverter_power_kw: float = 125  # inversores CSI-75K + CSI-50KTL-GI
    max_efficiency: float = 0.98  # 98% máxima (típico comercial)
    min_efficiency: float = 0.80  # 80% mínima (baixa carga)
    nominal_efficiency: float = 0.95  # 95% nominal (carga rated)

    voltage_loss_factor: float = 0.9901
    mppt_loss_factor: float = 0.9950


@dataclass
class DCLossCoefficients:
    a0: float = 0.015  # Perdas fixas base
    a1: float = -0.12  # Melhoria com irradiância
    a2: float = 0.28  # Perdas em alta irradiância

    a0_min: float = 0.005  # 0.5%
    a1_min: float = -0.25  # -25%
    a2_min: float = 0.15  # 15%

    a0_max: float = 0.08  # 8%
    a1_max: float = 0.02  # 2%
    a2_max: float = 0.45  # 45%


@dataclass
class ACLossCoefficients:
    """Coeficientes de perdas AC conforme NBR 16274 e dados PV*SOL."""

    wiring: float = 0.015  # 1.5% cabeamento AC
    transformer: float = 0.003  # 0.3% transformador (se houver)
    protection: float = 0.003  # 0.3% proteções (disjuntores, DPS)
    monitoring: float = 0.002  # 0.2% medição/monitoramento
    other: float = 0.002  # 0.2% outras perdas

    ac_loss: float = field(init=False)
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
    """Parâmetros para cálculos do sistema PV seguindo padrões ABNT NBR 16274:2014."""

    capacity_kwp: float = 125.0  # inversores CSI-75K + CSI-50KTL-GI
    noct: float = 42.0  # TNOC - Temperatura Nominal de Operação da Célula
    temp_coeff: float = -0.0037  # γ - Coeficiente de temperatura (%/°C)
    irrad_coeff: float = 0.031  # c - Coeficiente de irradiância
    constants: PVConstants = field(default_factory=PVConstants)
    inverter_coeffs: InverterCoefficients = field(default_factory=InverterCoefficients)
    dc_loss_coeffs: DCLossCoefficients = field(default_factory=DCLossCoefficients)
    ac_loss_coeffs: ACLossCoefficients = field(default_factory=ACLossCoefficients)


def create_system_parameters(capacity_kwp, noct, temp_coeff, irrad_coeff, dc_coeffs, inverter_coeffs, ac_losses=None):
    """Cria objeto PVSystemParameters com valores da interface."""

    dc_loss_coeffs = DCLossCoefficients(a0=dc_coeffs[0], a1=dc_coeffs[1], a2=dc_coeffs[2])

    inverter_coeffs_obj = InverterCoefficients(
        k0=inverter_coeffs[0],
        k1=inverter_coeffs[1],
        k2=inverter_coeffs[2],
        inverter_power_kw=capacity_kwp,
    )

    if ac_losses:
        ac_loss_coeffs = ACLossCoefficients(
            wiring=ac_losses[0],
            transformer=ac_losses[1],
            protection=ac_losses[2],
            monitoring=ac_losses[3],
            other=ac_losses[4],
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
