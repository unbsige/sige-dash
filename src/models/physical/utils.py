import numpy as np
import pandas as pd
import streamlit as st

from models.physical.coefficients import PVCoefficientOptimizer
from models.physical.evaluator import PVModelPerformanceEvaluator
from models.physical.params import PVSystemParameters
from models.physical.pv_model import PVBaselineModel


def calculate_performance_metrics(y_true, y_pred):
    mask = y_true >= 1.0
    y_true_filtered = y_true[mask]
    y_pred_filtered = y_pred[mask]

    if len(y_true_filtered) == 0:
        return {}

    mae = np.mean(np.abs(y_true_filtered - y_pred_filtered))
    rmse = np.sqrt(np.mean((y_true_filtered - y_pred_filtered) ** 2))
    mape = np.mean(np.abs((y_true_filtered - y_pred_filtered) / y_true_filtered)) * 100
    r2 = 1 - np.sum((y_true_filtered - y_pred_filtered) ** 2) / np.sum(
        (y_true_filtered - np.mean(y_true_filtered)) ** 2
    )
    mean_bias = np.mean(y_pred_filtered - y_true_filtered)
    mean_bias_pct = (mean_bias / np.mean(y_true_filtered)) * 100

    return {
        "MAE": mae,
        "RMSE": rmse,
        "MAPE": mape,
        "R²": r2,
        "Mean Bias": mean_bias,
        "Mean Bias (%)": mean_bias_pct,
        "N Points": len(y_true_filtered),
    }


def show_equation_popup(equation_type):
    """Mostra popup com equações e explicações"""
    equations = {
        "temperatura": {
            "title": "Temperatura da Célula (Eq. G.1)",
            "latex": r"T_c(i) = T_a(i) + \frac{G(i)}{800} \times (T_{NOC} - 20)",
            "explanation": """
            **Onde:**
            - Tc: temperatura da célula (°C)
            - Ta: temperatura ambiente (°C)  
            - G: irradiância GTI (W/m²)
            - TNOC: temperatura nominal de operação da célula (°C)
            
            **Função:** Estima a temperatura de operação das células fotovoltaicas
            baseada na temperatura ambiente e irradiância incidente.
            """,
        },
        "potencia_dc": {
            "title": "Potência DC Teórica (Eq. E.1)",
            "latex": r"P_{c.c.,teo}(i) = P_N \frac{G(i)}{1000} [1 + \gamma(T_c(i) - 25)] [1 + c \ln(\frac{G(i)}{1000})]",
            "explanation": """
            **Onde:**
            - PN: potência nominal do sistema (kWp)
            - γ: coeficiente de temperatura (%/°C)
            - c: coeficiente de irradiância
            
            **Função:** Calcula a potência DC teórica considerando correções
            por temperatura e resposta não-linear à irradiância.
            """,
        },
        "perdas_dc": {
            "title": "Cenário de Perdas DC (Anexo F)",
            "latex": r"CP_{c.c.} = \frac{G_{norm}}{G_{norm} + a_0 + a_1 \cdot G_{norm} + a_2 \cdot G_{norm}^2}",
            "explanation": """
            **Onde:**
            - Gnorm = G/1000: irradiância normalizada
            - a0: perdas fixas independentes da irradiância
            - a1: perdas/ganhos em baixa irradiância
            - a2: perdas em alta irradiância (quadráticas)
            
            **Função:** Modela as perdas DC do sistema em função da irradiância.
            """,
        },
        "eficiencia_inversor": {
            "title": "Eficiência do Inversor (Eq. E.2)",
            "latex": r"\eta_{inv} = \frac{-(k_1+1) + \sqrt{(k_1+1)^2 - 4k_2(k_0 - \frac{P_{c.c.}}{P_{NI}})}}{2k_2 \cdot \frac{P_{c.c.}}{P_{NI}}}",
            "explanation": """
            **Onde:**
            - PNI: potência nominal do inversor (kW)
            - k0, k1, k2: coeficientes da curva de eficiência
            - Pc.c.: potência DC ajustada (kW)
            
            **Função:** Calcula a eficiência do inversor em função da carga.
            """,
        },
    }

    eq = equations.get(equation_type, {})

    with st.expander(f"📖 {eq.get('title', 'Equação')}", expanded=False):
        st.latex(eq.get("latex", ""))
        st.markdown(eq.get("explanation", ""))


def calculate_energy_annual(df_power, capacity_kwp):
    """Calcula energia anual conforme metodologia NBR 16274.

    Implementa o cálculo da energia injetada na rede ao longo de um ano típico
    conforme Anexo G da NBR 16274.
    """

    annual_energy = df_power["ac_power_kw_est"].sum()
    capacity_factor = (annual_energy / (capacity_kwp * 8760)) * 100
    specific_energy = annual_energy / capacity_kwp

    return {
        "annual_energy_kwh": annual_energy,
        "capacity_factor_percent": capacity_factor,
        "specific_energy_kwh_per_kwp": specific_energy,
    }


def get_time_interval(df):
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("DataFrame must have DatetimeIndex")

    freq_infer = pd.infer_freq(df.index)
    freq_dataset = df.index.freqstr
    if freq_dataset and freq_dataset != freq_infer:
        print(f"Warning: Frequency mismatch! Dataset: {freq_dataset}, Inferred: {freq_infer}")

    if not freq_infer:
        raise ValueError("Could not detect data frequency. Index requires constant intervals.")

    try:
        delta_t = pd.Timedelta(df.index.freq).total_seconds() / 3600
        print(f"Detected frequency: {df.index.freq}")
        print(f"Using delta_t: {delta_t} hours")
        return delta_t
    except ValueError:
        raise ValueError(f"Detected frequency '{df.index.freq}' is not valid.")


def calculate_daily_energy(df, power_ac_col="power_ac_kw"):
    """Calculate daily energy from AC power data following ABNT NBR 16274:2014
    Implements Equation (7):
        E*_R = Σ P*_AC(i) · Δt (sum of instantaneous powers)

    Args:
        df_base: DataFrame with AC power data and DatetimeIndex
        power_ac_col: Column name for AC power data (kW)

    Returns:
        DataFrame with daily energy totals (kWh)
    """
    if power_ac_col not in df.columns:
        raise ValueError(f"Column '{power_ac_col}' not found in DataFrame")

    df = df.copy()
    delta_t = get_time_interval(df)

    if df[power_ac_col].isnull().any():
        print(f"Warning: {df[power_ac_col].isnull().sum()} null values found in column '{power_ac_col}'")
        df[power_ac_col] = df[power_ac_col].fillna(0)

    df["energy_kwh"] = df[power_ac_col] * delta_t
    return df["energy_kwh"].resample("D").sum().to_frame("daily_energy_kwh")
    # return df["energy_kwh"].resample("D").sum()
