import warnings

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import xgboost as xgb
from plotly import express as px
from plotly.subplots import make_subplots
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from src.config.settings import ML_CONFIG, PLANTS_CONFIG
from src.load_data import load_plant_data
from src.metrics import calculate_forecast_accuracy, print_forecast_accuracy
from src.models.physical.params import PVSystemParameters, create_system_parameters
from src.models.physical.run import run_pv_simulation

warnings.filterwarnings("ignore")

START_DATE = ML_CONFIG.get("START_DATE", "2020-01-01")
END_DATE = ML_CONFIG.get("END_DATE", "2023-12-31")
FEATURES = ML_CONFIG.get("FEATURES", [])
TARGET_COL = ML_CONFIG.get("TARGET_COL", "energy")
FREQUENCY = ML_CONFIG.get("FREQUENCY", "D")
XGB_PARAMS = ML_CONFIG.get("XGB_PARAMS", {})


def initialize_comparison_state():
    if "comparison_results" not in st.session_state:
        st.session_state.comparison_results = None
    if "ml_model" not in st.session_state:
        st.session_state.ml_model = None
    if "comparison_executed" not in st.session_state:
        st.session_state.comparison_executed = False


def convert_power_to_daily_energy(df_5min, power_col="ac_power_kw_est"):
    df_daily = df_5min.copy()

    # Converter potência para energia (kW * 5min / 60min = kWh)
    df_daily["energy_kwh"] = df_daily[power_col] * 5 / 60

    daily_energy = df_daily.groupby(df_daily.index.date)["energy_kwh"].sum()
    daily_energy.index = pd.to_datetime(daily_energy.index)
    return daily_energy


def add_temporal_features(df):
    df = df.copy()
    df["day"] = df.index.day
    df["month"] = df.index.month
    df["quarter"] = df.index.quarter
    df["day_of_year"] = df.index.dayofyear
    df["season"] = (df["month"] % 12) // 3 + 1
    return df


def add_time_since(df):
    df = df.copy()
    start_date = df.index.min()
    df["day_since"] = (df.index - start_date).days
    df["day_since_2"] = df["day_since"] ** 2
    return df


def add_cyclic_features(df):
    df = df.copy()
    df["day_of_year_sin"] = np.sin(2 * np.pi * df["day_of_year"] / 365.25)
    df["day_of_year_cos"] = np.cos(2 * np.pi * df["day_of_year"] / 365.25)
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
    return df


def create_solar_features(df):
    """Cria features solares específicas"""
    df_feat = df.copy()
    df_feat["csi_ghi"] = df_feat["ghi"] / df_feat["clearsky_ghi"].replace(0, np.nan)
    df_feat["csi_gti"] = df_feat["gti"] / df_feat["clearsky_gti"].replace(0, np.nan)
    df_feat["csi_mean"] = (df_feat["csi_ghi"] + df_feat["csi_gti"]) / 2
    df_feat["gti_net"] = df_feat["gti"] * df_feat["csi_mean"]
    df_feat["temp_loss"] = np.abs(df_feat["cell_temp"] - 25) * 0.004
    df_feat["cell_temp_mean"] = df_feat["cell_temp"]
    return df_feat


def create_features(df):
    df = add_temporal_features(df)
    df = add_time_since(df)
    df = add_cyclic_features(df)
    df = create_solar_features(df)
    return df


def prepare_daily_data(df_5min, observed_energy_col="energy"):
    daily_weather = df_5min.groupby(df_5min.index.date).agg({
        "ghi": "mean",
        "gti": "mean",
        "air_temp": "mean",
        "cell_temp": "mean",
        "clearsky_ghi": "mean",
        "clearsky_gti": "mean",
        "cloud_opacity": "mean",
    })
    daily_weather.index = pd.to_datetime(daily_weather.index)

    # Converter energia observada para diária (soma)
    if observed_energy_col in df_5min.columns:
        daily_observed = df_5min.groupby(df_5min.index.date)[observed_energy_col].sum() * 5 / 60  # kWh
        daily_observed.index = pd.to_datetime(daily_observed.index)
        daily_weather[TARGET_COL] = daily_observed

    # Criar features
    daily_data = create_features(daily_weather)

    return daily_data


def calculate_metrics(y_true, y_pred, model_name):
    mask = ~(pd.isna(y_true) | pd.isna(y_pred))  # Remover valores nulos
    y_true_clean = y_true[mask]
    y_pred_clean = y_pred[mask]

    if len(y_true_clean) == 0:
        return None

    mae = mean_absolute_error(y_true_clean, y_pred_clean)
    mse = mean_squared_error(y_true_clean, y_pred_clean)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_true_clean, y_pred_clean)

    # MAPE
    mape = np.mean(np.abs((y_true_clean - y_pred_clean) / np.maximum(y_true_clean, 0.1))) * 100

    return {"model": model_name, "mae": mae, "rmse": rmse, "r2": r2, "mape": mape, "n_samples": len(y_true_clean)}


# =====================================================================================================================
st.set_page_config(
    page_title="Físico vs ML - Detecção de Anomalias",
    page_icon="🔬",
    layout="wide",
)
st.title("🔬 Comparação: Modelo Físico vs Machine Learning")
st.markdown("**Detecção de Anomalias em Sistemas Fotovoltaicos - Análise Diária**")

if st.sidebar.button("🔄 Novo Experimento (Reset Geral)"):
    st.session_state.clear()
    st.rerun()

left_col, space, right_col = st.columns([4, 0.3, 7])

with left_col:
    selected_plant = st.selectbox(
        "Selecione a planta:",
        options=[""] + list(PLANTS_CONFIG.keys()),
        format_func=lambda x: "-- Selecione uma planta --"
        if x == ""
        else f"{PLANTS_CONFIG[x]['acronym']} - {PLANTS_CONFIG[x]['installed_capacity']} kWp",
        index=0,
    )
    if selected_plant:
        plant_config = PLANTS_CONFIG[selected_plant]
        data_key = f"df_data_{selected_plant}"
        if data_key not in st.session_state:
            with st.spinner(f"Carregando dados da {plant_config['acronym']}..."):
                st.session_state[data_key] = load_plant_data(selected_plant, "PT1D")

        df_data = st.session_state[data_key]
    else:
        st.stop()

with right_col:
    st.markdown("<br>", unsafe_allow_html=True)
    if selected_plant:
        default_params = PVSystemParameters(capacity_kwp=plant_config["installed_capacity"])

        st.markdown(f"#### {plant_config['name']}")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**Localização:** {plant_config['location']}")
            st.markdown(
                f"**Lat:** {plant_config.get('latitude', 'N/A')}° | **Lon:** {plant_config.get('longitude', 'N/A')}°"
            )

        with c2:
            st.markdown(f"**Potência Instalada:** {plant_config['installed_capacity']} kWp")
            st.markdown(
                f"**Inclinação:** {plant_config.get('tilt', 'N/A')}° | **Azimute:** {plant_config.get('azimuth', 'N/A')}°"
            )

st.write(" ")
st.divider()
st.markdown("</div>", unsafe_allow_html=True)

with st.expander("### ⚙️ Configuração do Experimento", expanded=False):
    initialize_comparison_state()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🤖 Machine Learning")
        st.markdown("**Período de Treinamento:**")
        st.info(f"📅 Início: `{START_DATE}`")
        st.info(f"📅 Fim: `{END_DATE}`")
        st.markdown("**Configuração:**")
        st.success(f"🎯 Target: `{TARGET_COL}`")
        features_display = ", ".join(FEATURES) if FEATURES else "Todas as disponíveis"
        st.success(f"🔧 Features: `{features_display}`")
        st.markdown("**Parâmetros XGBoost:**")
        for param, value in XGB_PARAMS.items():
            st.write(f"• `{param}`: {value}")

    with col2:
        st.markdown("#### ⚡ Modelo Físico")
        st.markdown("**Padrão NBR 16274:**")
        st.info("📋 Norma: NBR 16274 (ABNT)")
        st.info("🏭 Sistema: Fotovoltaico Grid-Tie")
        st.markdown("**Parâmetros Padrão:**")
        if selected_plant:
            st.success(f"🔋 Capacidade: `{plant_config['installed_capacity']} kWp`")
            st.success(f"📐 Inclinação: `{plant_config.get('tilt', 'Automática')}°`")
            st.success(f"🧭 Azimute: `{plant_config.get('azimuth', 'Sul (180°)')}°`")
            st.success("⚡ Eficiência: `85%` (padrão)")


st.markdown("**Modelo Físico:**")
use_default_physical = st.checkbox("Usar parâmetros padrão NBR 16274", value=True)


st.markdown("---")
if st.button("Executar Comparação Física vs ML", type="primary", use_container_width=True):
    try:
        with st.spinner("Executando simulação NBR 16274..."):
            df_5min = load_plant_data(selected_plant, "PT5M")

            default_params = PVSystemParameters(capacity_kwp=plant_config["installed_capacity"])

            with st.spinner("Executando simulação NBR 16274..."):
                results = run_pv_simulation(
                    df_data=df_5min,
                    params=default_params,
                )

                st.success("Simulação física concluída!")

            if results is None or results.empty:
                st.error("Erro na simulação física. Verifique os dados de entrada.")
                st.stop()

            df_physics_pred = pd.DataFrame(index=results.index)
            df_physics_pred_daily_true = convert_power_to_daily_energy(results, "energy")
            df_physics_pred_daily_pred = convert_power_to_daily_energy(results, "ac_power_kw_est")
            df_physics_pred_daily = pd.DataFrame({
                "y_true": df_physics_pred_daily_true,
                "y_pred": df_physics_pred_daily_pred,
            })

            # Dividir dados
            df_train = df_data.loc[str(START_DATE) : str(END_DATE)].copy()

            # Treinar modelo XGBoost
            available_features = [f for f in FEATURES if f in df_train.columns]
            X_train = df_train[available_features].fillna(0)
            y_train = df_train[TARGET_COL].fillna(0)

            xgb_model = xgb.XGBRegressor(**XGB_PARAMS)
            xgb_model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

            # Predições ML
            y_pred_ml = xgb_model.predict(X_test)

            # Modelo físico (simulação - substitua pela sua implementação)
            # Usar parâmetros padrão e converter para diário
            physical_power_5min = (
                df_5min.loc[str(test_start) : str(test_end)]["gti"] * 125 * 0.85 / 1000
            )  # Simulação simplificada
            y_pred_physical = convert_power_to_daily_energy(
                pd.DataFrame({"ac_power_kw_est": physical_power_5min}, index=physical_power_5min.index)
            )

            # Alinhar índices
            common_dates = y_test.index.intersection(y_pred_physical.index)
            y_test_aligned = y_test.loc[common_dates]
            y_pred_ml_aligned = y_pred_ml[y_test.index.isin(common_dates)]
            y_pred_physical_aligned = y_pred_physical.loc[common_dates]

            # Salvar resultados
            results = pd.DataFrame(
                {
                    "date": common_dates,
                    "observed": y_test_aligned.values,
                    "ml_pred": y_pred_ml_aligned,
                    "physical_pred": y_pred_physical_aligned.values,
                },
                index=common_dates,
            )

            st.session_state.comparison_results = results
            st.session_state.ml_model = xgb_model
            st.session_state.comparison_executed = True

        st.success("✅ Comparação executada com sucesso!")

    except Exception as e:
        st.error(f"❌ Erro na comparação: {str(e)}")
        st.info("Verifique os dados e configurações.")

# Mostrar resultados se disponíveis
if st.session_state.comparison_results is not None:
    results = st.session_state.comparison_results

    st.markdown("---")
    st.markdown("### 📊 Resultados da Comparação")

    # Calcular métricas
    metrics_ml = calculate_metrics(results["observed"], results["ml_pred"], "XGBoost ML")
    metrics_physical = calculate_metrics(results["observed"], results["physical_pred"], "Modelo Físico")

    # Cards de métricas
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("R² ML", f"{metrics_ml['r2']:.3f}")
        st.metric("R² Físico", f"{metrics_physical['r2']:.3f}")

    with col2:
        st.metric("MAE ML", f"{metrics_ml['mae']:.2f} kWh")
        st.metric("MAE Físico", f"{metrics_physical['mae']:.2f} kWh")

    with col3:
        st.metric("MAPE ML", f"{metrics_ml['mape']:.1f}%")
        st.metric("MAPE Físico", f"{metrics_physical['mape']:.1f}%")

    with col4:
        st.metric("Amostras", f"{metrics_ml['n_samples']}")
        st.metric("Período", f"{len(results)} dias")

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=results.index,
            y=results["observed"],
            mode="lines",
            name="Observado",
            line=dict(color="black", width=2),
            hovertemplate="<b>Observado</b><br>%{x}<br>%{y:.2f} kWh<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=results.index,
            y=results["ml_pred"],
            mode="lines",
            name="XGBoost ML",
            line=dict(color="blue", width=2, dash="dash"),
            hovertemplate="<b>ML</b><br>%{x}<br>%{y:.2f} kWh<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=results.index,
            y=results["physical_pred"],
            mode="lines",
            name="Modelo Físico",
            line=dict(color="red", width=2, dash="dot"),
            hovertemplate="<b>Físico</b><br>%{x}<br>%{y:.2f} kWh<extra></extra>",
        )
    )

    fig.add_vrect(
        x0=INVERTER_ISSUE_START_DATE,
        x1=INVERTER_ISSUE_END_DATE,
        fillcolor="rgba(255,0,0,0.1)",
        layer="below",
        line_width=0,
        annotation_text="Período de Anomalia",
        annotation_position="top left",
    )

    fig.update_layout(
        title="Comparação: Energia Diária - Observada vs Predições",
        xaxis_title="Data",
        yaxis_title="Energia (kWh/dia)",
        hovermode="x unified",
        height=500,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 🎯 Análise de Correlação")

    fig_scatter = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=["XGBoost ML vs Observado", "Modelo Físico vs Observado"],
        horizontal_spacing=0.1,
    )

    fig_scatter.add_trace(
        go.Scatter(
            x=results["observed"],
            y=results["ml_pred"],
            mode="markers",
            name="ML",
            marker=dict(color="blue", size=6, opacity=0.7),
            hovertemplate="Obs: %{x:.2f}<br>ML: %{y:.2f}<extra></extra>",
        ),
        row=1,
        col=1,
    )

    fig_scatter.add_trace(
        go.Scatter(
            x=results["observed"],
            y=results["physical_pred"],
            mode="markers",
            name="Físico",
            marker=dict(color="red", size=6, opacity=0.7),
            hovertemplate="Obs: %{x:.2f}<br>Físico: %{y:.2f}<extra></extra>",
        ),
        row=1,
        col=2,
    )

    max_val = max(results["observed"].max(), results["ml_pred"].max(), results["physical_pred"].max())
    for col in [1, 2]:
        fig_scatter.add_trace(
            go.Scatter(
                x=[0, max_val],
                y=[0, max_val],
                mode="lines",
                name="Predição Perfeita",
                line=dict(color="gray", dash="dash"),
                showlegend=(col == 1),
            ),
            row=1,
            col=col,
        )

    fig_scatter.update_layout(height=400, title_text="Correlação entre Predições e Valores Observados")

    fig_scatter.update_xaxes(title_text="Energia Observada (kWh)")
    fig_scatter.update_yaxes(title_text="Energia Predita (kWh)")

    st.plotly_chart(fig_scatter, use_container_width=True)

    st.markdown("### 🚨 Detecção de Anomalias")
    results["error_ml"] = np.abs(results["observed"] - results["ml_pred"])
    results["error_physical"] = np.abs(results["observed"] - results["physical_pred"])

    threshold_ml = results["error_ml"].mean() + 2 * results["error_ml"].std()
    threshold_physical = results["error_physical"].mean() + 2 * results["error_physical"].std()

    anomalies_ml = results["error_ml"] > threshold_ml
    anomalies_physical = results["error_physical"] > threshold_physical

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Anomalias ML", f"{anomalies_ml.sum()}/{len(results)}")

    with col2:
        st.metric("Anomalias Físico", f"{anomalies_physical.sum()}/{len(results)}")

    with col3:
        known_anomaly_period = (results.index >= INVERTER_ISSUE_START_DATE) & (
            results.index <= INVERTER_ISSUE_END_DATE
        )
        overlap_ml = (anomalies_ml & known_anomaly_period).sum()
        overlap_physical = (anomalies_physical & known_anomaly_period).sum()
        st.metric("Detecção no Período", f"ML: {overlap_ml}, Físico: {overlap_physical}")

    st.markdown("---")
    csv = results.to_csv()
    st.download_button(
        label="Download Resultados Comparação",
        data=csv,
        file_name=f"comparacao_fisico_ml_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
    )

    with st.expander("📋 Métricas Detalhadas"):
        metrics_df = pd.DataFrame([metrics_ml, metrics_physical])
        st.dataframe(metrics_df, use_container_width=True)
