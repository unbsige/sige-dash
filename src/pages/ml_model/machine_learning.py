import warnings

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import xgboost as xgb
from plotly.subplots import make_subplots
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from src.config.settings import ML_CONFIG, PLANTS_CONFIG
from src.load_data import load_plant_data
from src.metrics import calculate_forecast_accuracy
from src.models.physical.params import PVSystemParameters
from src.models.physical.run import run_pv_simulation

warnings.filterwarnings("ignore")

START_DATE = ML_CONFIG.get("START_DATE", "2020-01-01")
END_DATE = ML_CONFIG.get("END_DATE", "2023-12-31")
FEATURES = ML_CONFIG.get("FEATURES", [])
TARGET_COL = ML_CONFIG.get("TARGET_COL", "energy")
XGB_PARAMS = ML_CONFIG.get("XGB_PARAMS", {})

INVERTER_ISSUE_START_DATE = "2022-09-14"
INVERTER_ISSUE_END_DATE = "2022-10-31"


def initialize_comparison_state():
    """Inicializa variáveis do session state"""
    if "comparison_results" not in st.session_state:
        st.session_state.comparison_results = None
    if "ml_model" not in st.session_state:
        st.session_state.ml_model = None
    if "comparison_executed" not in st.session_state:
        st.session_state.comparison_executed = False


def convert_power_to_daily_energy(df_5min, power_col="ac_power_kw_est"):
    """Converte dados de potência de 5 minutos para energia diária em kWh"""
    df_daily = df_5min.copy()
    df_daily["energy_kwh"] = df_daily[power_col] * 5 / 60  # kW * 5min / 60min = kWh
    daily_energy = df_daily.groupby(df_daily.index.date)["energy_kwh"].sum()
    daily_energy.index = pd.to_datetime(daily_energy.index)
    return daily_energy


def add_temporal_features(df):
    """Adiciona features temporais"""
    df = df.copy()
    df["day"] = df.index.day
    df["month"] = df.index.month
    df["quarter"] = df.index.quarter
    df["day_of_year"] = df.index.dayofyear
    df["season"] = (df["month"] % 12) // 3 + 1
    return df


def add_time_since(df):
    """Adiciona features de tempo decorrido"""
    df = df.copy()
    start_date = df.index.min()
    df["day_since"] = (df.index - start_date).days
    df["day_since_2"] = df["day_since"] ** 2
    return df


def add_cyclic_features(df):
    """Adiciona features cíclicas"""
    df = df.copy()
    df["day_of_year_sin"] = np.sin(2 * np.pi * df["day_of_year"] / 365.25)
    df["day_of_year_cos"] = np.cos(2 * np.pi * df["day_of_year"] / 365.25)
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
    return df


def create_solar_features(df):
    """Cria features solares específicas"""
    df_feat = df.copy()
    # Clear Sky Index
    df_feat["csi_ghi"] = df_feat["ghi"] / df_feat["clearsky_ghi"].replace(0, np.nan)
    df_feat["csi_gti"] = df_feat["gti"] / df_feat["clearsky_gti"].replace(0, np.nan)
    df_feat["csi_mean"] = (df_feat["csi_ghi"] + df_feat["csi_gti"]) / 2
    df_feat["gti_net"] = df_feat["gti"] * df_feat["csi_mean"]
    df_feat["temp_loss"] = np.abs(df_feat["cell_temp"] - 25) * 0.004
    df_feat["cell_temp_mean"] = df_feat["cell_temp"]
    return df_feat


def create_features(df):
    """Pipeline completo de criação de features"""
    df = add_temporal_features(df)
    df = add_time_since(df)
    df = add_cyclic_features(df)
    # df = create_solar_features(df)
    return df


def prepare_daily_data_for_ml(df_5min, observed_energy_col="energy"):
    """Prepara dados diários a partir de dados de 5 minutos para ML"""
    # Converter dados meteorológicos para diários (média)
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

    # Converter energia observada para diária se disponível
    if observed_energy_col in df_5min.columns:
        daily_observed = df_5min.groupby(df_5min.index.date)[observed_energy_col].sum() * 5 / 60
        daily_observed.index = pd.to_datetime(daily_observed.index)
        daily_weather[TARGET_COL] = daily_observed

    # Criar features para ML
    daily_data = create_features(daily_weather)
    return daily_data


def calculate_metrics(y_true, y_pred, model_name):
    """Calcula métricas de avaliação"""
    mask = ~(pd.isna(y_true) | pd.isna(y_pred))
    y_true_clean = y_true[mask]
    y_pred_clean = y_pred[mask]

    if len(y_true_clean) == 0:
        return None

    mae = mean_absolute_error(y_true_clean, y_pred_clean)
    mse = mean_squared_error(y_true_clean, y_pred_clean)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_true_clean, y_pred_clean)
    mape = np.mean(np.abs((y_true_clean - y_pred_clean) / np.maximum(y_true_clean, 0.1))) * 100

    return {"model": model_name, "mae": mae, "rmse": rmse, "r2": r2, "mape": mape, "n_samples": len(y_true_clean)}


# =====================================================================================================================
# APLICAÇÃO PRINCIPAL
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

st.divider()

with st.expander("⚙️ Configuração do Experimento", expanded=False):
    initialize_comparison_state()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🤖 Machine Learning")
        st.markdown("**Período de Treinamento:**")
        st.info(f"📅 Início: `{START_DATE}`")
        st.info(f"📅 Fim: `{END_DATE}`")
        st.markdown("**Configuração:**")
        st.success(f"🎯 Target: `{TARGET_COL}`")
        features_display = ", ".join(FEATURES[:3]) + "..." if len(FEATURES) > 3 else ", ".join(FEATURES)
        st.success(f"🔧 Features: `{features_display}`")

        if XGB_PARAMS:
            st.markdown("**Principais Parâmetros XGBoost:**")
            key_params = ["learning_rate", "max_depth", "n_estimators"]
            for param in key_params:
                if param in XGB_PARAMS:
                    st.write(f"• `{param}`: {XGB_PARAMS[param]}")

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

st.markdown("### 📅 Período de Análise")
col1, col2 = st.columns(2)

with col1:
    analysis_start = st.date_input(
        "Data Início", value=pd.to_datetime("2025-01-01").date(), help="Período para comparação dos modelos"
    )

with col2:
    analysis_end = st.date_input(
        "Data Fim", value=pd.to_datetime("2025-03-31").date(), help="Fim do período de análise"
    )

if analysis_start >= analysis_end:
    st.error("Data de início deve ser anterior à data de fim")
    st.stop()

st.markdown("---")
if st.button("🚀 Executar Comparação Física vs ML", type="primary", use_container_width=True):
    try:
        with st.spinner("Preparando dados e executando comparações..."):
            st.info("📊 Carregando dados de 5 minutos...")
            df_5min = load_plant_data(selected_plant, "PT5M")
            df_5min_filtered = df_5min.loc[str(analysis_start) : str(analysis_end)].copy()

            if df_5min_filtered.empty:
                st.error("Nenhum dado encontrado para o período selecionado")
                st.stop()

            st.info("⚡ Executando simulação do modelo físico NBR 16274...")
            default_params = PVSystemParameters(capacity_kwp=plant_config["installed_capacity"])

            physical_results = run_pv_simulation(
                df_data=df_5min_filtered,
                params=default_params,
                apply_dc_losses=True,
                apply_ac_losses=True,
                use_nbr_efficiency=True,
            )

            if physical_results is None or physical_results.empty:
                st.error("Erro na simulação física. Verifique os dados de entrada.")
                st.stop()

            st.info("🔄 Convertendo dados para energia diária...")
            daily_observed = convert_power_to_daily_energy(physical_results, "energy")
            daily_physical_pred = convert_power_to_daily_energy(physical_results, "ac_power_kw_est")

            # 4. Preparar dados para ML
            # st.info("🤖 Preparando dados para modelo ML...")
            # df_daily_ml = prepare_daily_data_for_ml(df_5min_filtered, "energy")

            # 5. Treinar modelo XGBoost com dados históricos
            st.info("🧠 Treinando modelo XGBoost...")
            st.dataframe(df_data.head(), width="stretch")

            df_data_feat = create_features(df_data)
            df_train = df_data_feat.loc[START_DATE:END_DATE].copy()

            if df_train.empty or TARGET_COL not in df_train.columns:
                st.error("Dados históricos de treinamento não disponíveis")
                st.stop()

            available_features = [f for f in FEATURES if f in df_train.columns]
            missing_features = [f for f in FEATURES if f not in df_train.columns]

            if missing_features:
                st.warning(f"Features ausentes: {', '.join(missing_features)}")

            if not available_features:
                st.error("Nenhuma feature disponível para treinamento")
                st.stop()

            X_train = df_train[available_features].fillna(0)
            y_train = df_train[TARGET_COL].fillna(0)

            xgb_model = xgb.XGBRegressor(**XGB_PARAMS)
            xgb_model.fit(X_train, y_train, verbose=False)

            st.info("🔮 Gerando predições do modelo ML...")
            prediction_features = [f for f in available_features if f in df_data_feat.columns]
            st.write(f"prediction_features: {', '.join(prediction_features)}")

            X_prediction = df_data_feat[prediction_features].fillna(0)
            st.write(f"X_prediction: {X_prediction}")

            daily_ml_pred = xgb_model.predict(X_prediction)
            daily_ml_pred = pd.Series(daily_ml_pred, index=df_data_feat.index)

            # 7. Alinhar dados
            st.info("🔗 Alinhando dados para comparação...")
            common_dates = daily_observed.index.intersection(daily_physical_pred.index).intersection(
                daily_ml_pred.index
            )

            if len(common_dates) == 0:
                st.error("Nenhuma data comum encontrada entre os datasets")
                st.stop()

            # Criar DataFrame final
            comparison_results = pd.DataFrame(
                {
                    "observed": daily_observed.loc[common_dates].values,
                    "physical_pred": daily_physical_pred.loc[common_dates].values,
                    "ml_pred": daily_ml_pred.loc[common_dates].values,
                },
                index=common_dates,
            )

            comparison_results = comparison_results.dropna()

            if comparison_results.empty:
                st.error("Nenhum dado válido após limpeza")
                st.stop()

            # Salvar resultados
            st.session_state.comparison_results = comparison_results
            st.session_state.ml_model = xgb_model
            st.session_state.comparison_executed = True
            st.session_state.analysis_period = (analysis_start, analysis_end)

        st.success("✅ Comparação executada com sucesso!")
        st.info(f"📊 Período analisado: {len(comparison_results)} dias")

    except Exception as e:
        st.error(f"❌ Erro na comparação: {str(e)}")
        st.info("Verifique os dados e configurações.")

# Mostrar resultados se disponíveis
if st.session_state.get("comparison_executed", False) and st.session_state.get("comparison_results") is not None:
    results = st.session_state.comparison_results

    st.markdown("---")
    st.markdown("### 📊 Resultados da Comparação")

    # Calcular métricas
    metrics_ml = calculate_metrics(results["observed"], results["ml_pred"], "XGBoost ML")
    metrics_physical = calculate_metrics(results["observed"], results["physical_pred"], "Modelo Físico NBR 16274")

    # Cards de métricas
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("R² ML", f"{metrics_ml['r2']:.3f}")
        st.metric(
            "R² Físico", f"{metrics_physical['r2']:.3f}", delta=f"{metrics_physical['r2'] - metrics_ml['r2']:+.3f}"
        )

    with col2:
        st.metric("MAE ML", f"{metrics_ml['mae']:.2f} kWh")
        st.metric(
            "MAE Físico",
            f"{metrics_physical['mae']:.2f} kWh",
            delta=f"{metrics_physical['mae'] - metrics_ml['mae']:+.2f}",
        )

    with col3:
        st.metric("MAPE ML", f"{metrics_ml['mape']:.1f}%")
        st.metric(
            "MAPE Físico",
            f"{metrics_physical['mape']:.1f}%",
            delta=f"{metrics_physical['mape'] - metrics_ml['mape']:+.1f}%",
        )

    with col4:
        st.metric("Amostras", f"{metrics_ml['n_samples']}")
        st.metric("Período", f"{len(results)} dias")

    # Gráfico principal de comparação
    fig = go.Figure()

    # Linha observada
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

    # Linha ML
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

    # Linha física
    fig.add_trace(
        go.Scatter(
            x=results.index,
            y=results["physical_pred"],
            mode="lines",
            name="Modelo Físico NBR 16274",
            line=dict(color="red", width=2, dash="dot"),
            hovertemplate="<b>Físico</b><br>%{x}<br>%{y:.2f} kWh<extra></extra>",
        )
    )

    # Destacar período de anomalia se estiver no range
    if (
        pd.to_datetime(INVERTER_ISSUE_START_DATE) >= results.index.min()
        and pd.to_datetime(INVERTER_ISSUE_END_DATE) <= results.index.max()
    ):
        fig.add_vrect(
            x0=INVERTER_ISSUE_START_DATE,
            x1=INVERTER_ISSUE_END_DATE,
            fillcolor="rgba(255,0,0,0.1)",
            layer="below",
            line_width=0,
            annotation_text="Período de Anomalia Conhecida",
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

    # Gráfico de correlação
    st.markdown("### 🎯 Análise de Correlação")

    fig_scatter = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=["XGBoost ML vs Observado", "Modelo Físico vs Observado"],
        horizontal_spacing=0.1,
    )

    # Scatter ML
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

    # Scatter Físico
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

    # Linha diagonal perfeita
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

    # Análise de detecção de anomalias
    st.markdown("### 🚨 Detecção de Anomalias")

    # Calcular erros
    results["error_ml"] = np.abs(results["observed"] - results["ml_pred"])
    results["error_physical"] = np.abs(results["observed"] - results["physical_pred"])

    # Definir thresholds
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
        # Verificar detecção no período conhecido de anomalia
        known_anomaly_period = (results.index >= INVERTER_ISSUE_START_DATE) & (
            results.index <= INVERTER_ISSUE_END_DATE
        )
        overlap_ml = (anomalies_ml & known_anomaly_period).sum()
        overlap_physical = (anomalies_physical & known_anomaly_period).sum()
        st.metric("Detecção no Período", f"ML: {overlap_ml}, Físico: {overlap_physical}")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        csv = results.to_csv()
        st.download_button(
            label="📥 Download Resultados Comparação",
            data=csv,
            file_name=f"comparacao_fisico_ml_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col2:
        with st.expander("📋 Métricas Detalhadas"):
            metrics_df = pd.DataFrame([metrics_ml, metrics_physical])
            st.dataframe(metrics_df, use_container_width=True)
