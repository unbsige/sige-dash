import warnings
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from src.models.physical.coefficients import PVCoefficientOptimizer
from src.models.physical.evaluator import PVModelPerformanceEvaluator
from src.models.physical.params import PVSystemParameters
from src.models.physical.pv_model import PVBaselineModel


def generate_sample_data_with_real():
    """Gera dados sintéticos com 'valores reais' simulados"""
    dates = pd.date_range("2024-01-01", "2024-12-31", freq="H")

    hour_of_day = dates.hour
    day_of_year = dates.dayofyear

    base_irradiance = np.maximum(0, 800 * np.sin(np.pi * (hour_of_day - 6) / 12))
    seasonal_factor = 0.8 + 0.4 * np.sin(2 * np.pi * (day_of_year - 80) / 365)
    cloud_factor = 0.7 + 0.3 * np.random.random(len(dates))
    gti = base_irradiance * seasonal_factor * cloud_factor
    gti = np.maximum(0, gti)

    seasonal_temp = 25 + 10 * np.sin(2 * np.pi * (day_of_year - 80) / 365)
    daily_temp_variation = 5 * np.sin(np.pi * (hour_of_day - 6) / 12)
    air_temp = seasonal_temp + daily_temp_variation + np.random.normal(0, 2, len(dates))

    df_temp = pd.DataFrame({"gti": gti, "air_temp": air_temp}, index=dates)

    real_model = PVBaselineModel(PVSystemParameters())
    real_coeffs = {"a0": 0.015, "a1": -0.12, "a2": 0.25}
    df_real = real_model.calculate_ac_power(df_temp, real_coeffs)

    noise_factor = 0.05  # 5% de ruído
    df_real["ac_power_kw_real"] = df_real["ac_power_kw_est"] * (1 + np.random.normal(0, noise_factor, len(df_real)))
    df_real["ac_power_kw_real"] = np.maximum(0, df_real["ac_power_kw_real"])

    return df_real[["gti", "air_temp", "ac_power_kw_real"]]


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


def run_optimization_analysis(df_dropna, initial_coeffs, pv_model, params):
    """Executa análise completa de otimização com diferentes métodos."""
    optimizer = PVCoefficientOptimizer(
        pv_model=pv_model,
        params=params,
        irrad_col="gti",
        air_temp_col="air_temp",
        power_col="ac_power_kw",
    )

    try:
        result = optimizer.calibrate_with_ac_data(df=df_dropna, initial_coeffs=initial_coeffs)
        if result["success"]:
            result["metrics"] = validate_optimization_result(df_dropna, pv_model, result["optimized_coeffs"])
    except Exception as e:
        print(f"Erro durante otimização: {e}")
        result = {"success": False, "error": str(e)}

    return result


def validate_optimization_result(df, pv_model, optimized_coeffs):
    validator = PVModelPerformanceEvaluator(pv_model)
    metrics = validator.evaluate_coefficients(
        df,
        optimized_coeffs,
        irrad_col="gti",
        air_temp_col="air_temp",
        power_ac_col="ac_power_kw",
    )

    print("")
    print("--" * 50)
    print(" => ANÁLISE DE OTIMIZAÇÃO DE COEFICIENTES")
    print("--" * 50)

    print("\n => Coeficientes otimizados:")
    print(f"  - a0: {optimized_coeffs['a0']:.3f}")
    print(f"  - a1: {optimized_coeffs['a1']:.3f}")
    print(f"  - a2: {optimized_coeffs['a2']:.3f}")

    print("\n => Métricas de validação:")
    print(f"  - MAE  : {metrics['mae']:.3f} W")
    print(f"  - nMAE : {metrics['nmae']:.3f}%")
    print(f"  - RMSE : {metrics['rmse']:.3f} W")
    print(f"  - nRMSE: {metrics['nrmse']:.3f} W")
    print(f"  - Bias : {metrics['mean_bias']:.3f} W")
    print(f"  - R²   : {metrics['r2_score']:.3f}")
    print("--" * 50)
    return metrics


def compare_results(m_ini, m_opt):
    mae_diff = float(m_ini["mae"] - m_opt["mae"])
    nmae_diff = float(m_ini["nmae"] - m_opt["nmae"])
    rmse_diff = float(m_ini["rmse"] - m_opt["rmse"])
    nrmse_diff = float(m_ini["nrmse"] - m_opt["nrmse"])
    bias_diff = float(m_ini["mean_bias"] - m_opt["mean_bias"])
    r2_diff = float(m_opt["r2_score"] - m_ini["r2_score"])

    mae_pct = 100 * mae_diff / m_ini["mae"] if m_ini["mae"] != 0 else 0
    rmse_pct = 100 * rmse_diff / m_ini["rmse"] if m_ini["rmse"] != 0 else 0
    nmae_pct = 100 * nmae_diff / m_ini["nmae"] if m_ini["nmae"] != 0 else 0
    nrmse_pct = 100 * nrmse_diff / m_ini["nrmse"] if m_ini["nrmse"] != 0 else 0
    bias_pct = (
        100 * (abs(m_ini["mean_bias"]) - abs(m_opt["mean_bias"])) / abs(m_ini["mean_bias"])
        if m_ini["mean_bias"] != 0
        else 0
    )

    print("\nCOMPARAÇÃO DE RESULTADOS:")
    print("-" * 70)
    print(f"{'Métrica':^10} | {'Inicial':^12} | {'Otimizado':^12} | {'Δ':^10} | {'Δ (%)':^10}")
    print("-" * 70)
    print(f"{'MAE (W)':<10} | {m_ini['mae']:<12.3f} | {m_opt['mae']:<12.3f} | {mae_diff:<10.3f} | {mae_pct:<10.2f}")
    print(
        f"{'nMAE (%)':<10} | {m_ini['nmae']:<12.2f} | {m_opt['nmae']:<12.2f} | {nmae_diff:<10.2f} | {nmae_pct:<10.2f}"
    )
    print(
        f"{'RMSE (W)':<10} | {m_ini['rmse']:<12.3f} | {m_opt['rmse']:<12.3f} | {rmse_diff:<10.3f} | {rmse_pct:<10.2f}"
    )
    print(
        f"{'nRMSE (%)':<10} | {m_ini['nrmse']:<12.4f} | {m_opt['nrmse']:<12.4f} | {nrmse_diff:<10.4f} | {nrmse_pct:<10.2f}"
    )
    print(
        f"{'Bias (W)':<10} | {m_ini['mean_bias']:<12.3f} | {m_opt['mean_bias']:<12.3f} | {bias_diff:<10.3f} | {bias_pct:<10.2f}"
    )
    print(f"{'R²':<10} | {m_ini['r2_score']:<12.4f} | {m_opt['r2_score']:<12.4f} | {r2_diff:<10.4f} | {'':<10}")
    print("-" * 70)
