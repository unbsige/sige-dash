import pandas as pd

from src.pages.physical_model.coefficients import PVCoefficientOptimizer
from src.pages.physical_model.evaluator import PVModelPerformanceEvaluator


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
        100 * (abs(m_ini["mean_bias"]) - abs(m_opt["mean_bias"])) / abs(m_ini["mean_bias"]) if m_ini["mean_bias"] != 0 else 0
    )

    print("\nCOMPARAÇÃO DE RESULTADOS:")
    print("-" * 70)
    print(f"{'Métrica':^10} | {'Inicial':^12} | {'Otimizado':^12} | {'Δ':^10} | {'Δ (%)':^10}")
    print("-" * 70)
    print(f"{'MAE (W)':<10} | {m_ini['mae']:<12.3f} | {m_opt['mae']:<12.3f} | {mae_diff:<10.3f} | {mae_pct:<10.2f}")
    print(f"{'nMAE (%)':<10} | {m_ini['nmae']:<12.2f} | {m_opt['nmae']:<12.2f} | {nmae_diff:<10.2f} | {nmae_pct:<10.2f}")
    print(f"{'RMSE (W)':<10} | {m_ini['rmse']:<12.3f} | {m_opt['rmse']:<12.3f} | {rmse_diff:<10.3f} | {rmse_pct:<10.2f}")
    print(f"{'nRMSE (%)':<10} | {m_ini['nrmse']:<12.4f} | {m_opt['nrmse']:<12.4f} | {nrmse_diff:<10.4f} | {nrmse_pct:<10.2f}")
    print(
        f"{'Bias (W)':<10} | {m_ini['mean_bias']:<12.3f} | {m_opt['mean_bias']:<12.3f} | {bias_diff:<10.3f} | {bias_pct:<10.2f}"
    )
    print(f"{'R²':<10} | {m_ini['r2_score']:<12.4f} | {m_opt['r2_score']:<12.4f} | {r2_diff:<10.4f} | {'':<10}")
    print("-" * 70)
