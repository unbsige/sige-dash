import warnings

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly import express as px
from plotly.subplots import make_subplots
from sklearn.metrics import r2_score

from pages.physical_model.components.analyzer import daily_pv_curve_analyzer
from pages.physical_model.components.charts import (
    create_preview_chart,
    display_simulation_results,
    show_meteorological_preview,
)
from pages.physical_model.components.results import plot_metrics
from src.config.settings import PLANTS_CONFIG
from src.load_data import get_plant_defaults, load_plant_data
from src.metrics import calculate_forecast_accuracy, print_forecast_accuracy
from src.models.physical.params import PVSystemParameters, create_system_parameters
from src.models.physical.run import run_pv_simulation

warnings.filterwarnings("ignore")


st.set_page_config(
    page_title="Simulador PV NBR 16274",
    page_icon="☀️",
    layout="wide",
)

st.set_page_config(page_title="Simulador PV NBR 16274", layout="wide")

st.title(" Simulador de Sistemas Fotovoltaicos NBR 16274:2014")
st.markdown("**Simulação conforme norma brasileira para sistemas conectados à rede - Campus UnB**")

st.markdown('<div class="nbr-highlight">', unsafe_allow_html=True)
st.markdown("### 1. Seleção da Planta Fotovoltaica")
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
                st.session_state[data_key] = load_plant_data(selected_plant, "PT5M")

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

with st.expander(" Localização e Vista da Instalação"):
    col1, col2 = st.columns(2)

    with col1:
        try:
            photo_path = "assets/campus_fcte_uac.jpeg"
            st.image(photo_path, caption=f"Vista da {plant_config['acronym']}")
        except:
            st.info(f"📷 Foto da {plant_config['acronym']} não disponível")

    with col2:
        if plant_config.get("latitude") and plant_config.get("longitude"):
            lat = plant_config["latitude"]
            lon = plant_config["longitude"]

            fig_map = go.Figure(
                go.Scattermapbox(
                    lat=[lat],
                    lon=[lon],
                    mode="markers",
                    marker=go.scattermapbox.Marker(size=10, color="red"),
                    text=[f"{plant_config['acronym']} - {plant_config['installed_capacity']} kWp"],
                    hoverinfo="text",
                )
            )

            fig_map.update_layout(
                mapbox_style="open-street-map",
                mapbox=dict(center=go.layout.mapbox.Center(lat=lat, lon=lon), zoom=17),
                showlegend=False,
                height=415,
                margin={"r": 0, "t": 0, "l": 0, "b": 0},
            )

            st.plotly_chart(fig_map, width="stretch")
        else:
            st.warning("⚠️ Coordenadas não disponíveis para esta planta")

st.markdown("</div>", unsafe_allow_html=True)
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------------------------------------------------
# sidebar - configurações gerais
# ---------------------------------------------------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="sidebar-header">⚙️ Configurações</div>', unsafe_allow_html=True)
    apply_dc_losses = st.checkbox(
        "   Aplicar perdas DC", value=True, help="Se desmarcado, considera sistema sem perdas DC"
    )
    apply_ac_losses = st.checkbox(
        "   Aplicar perdas AC", value=True, help="Se desmarcado, considera sistema sem perdas AC"
    )
    use_nbr_efficiency = st.checkbox(
        "Usar eficiência NBR 16274", value=True, help="Se desmarcado, usa dados do PV*SOL"
    )

    if st.button(" Recarregar Dados da Planta"):
        if f"df_data_{selected_plant}" in st.session_state:
            del st.session_state[f"df_data_{selected_plant}"]
        st.rerun()


# ----------------------------------------------------------------------------------------------------------------
# ETAPA 2: PERÍODO DE ANÁLISE + PREVIEW
# ----------------------------------------------------------------------------------------------------------------
st.markdown("#### Período de Análise")
min_date = df_data.index.min().date()
max_date = df_data.index.max().date()

years = df_data.index.year.unique()
years = df_data.index.year.unique()
year_options = ["todos"] + years.tolist()

col1, col2, _, col3 = st.columns([4, 4, 2, 20])
with col1:
    selected_year = st.selectbox("Ano:", options=year_options, index=len(year_options) - 1)

    if selected_year != "todos":
        df_year = df_data[df_data.index.year == selected_year]
    else:
        df_year = df_data.copy()

    months_options = ["todos"] + df_year.index.month.unique().tolist()

with col2:
    selected_month = st.selectbox(
        "Mês",
        options=months_options,
        index=0,
        help="Selecione o mês para visualizar os gráficos",
    )

    if selected_month != "todos":
        df_month = df_year[df_year.index.month == selected_month]
    else:
        df_month = df_year.copy()

with col3.container():
    start_date, end_date = st.slider(
        "Selecione o intervalo:",
        min_value=df_month.index.min().date(),
        max_value=df_month.index.max().date(),
        value=(df_month.index.min().date(), df_month.index.max().date()),
        step=None,
        format="DD/MM/YYYY",
        help="Selecione o intervalo para visualizar os gráficos",
    )

st.write(" ")
df_filtered = df_data.loc[start_date:end_date].copy()
fig_preview = create_preview_chart(df_filtered, start_date, end_date)
st.plotly_chart(fig_preview, width="stretch")

st.write(" ")
st.divider()


left_col, space, right_col = st.columns([2, 0.4, 8])
with left_col:
    st.markdown("#####  Parâmetros do Sistema")

    with st.container(border=True):
        noct = st.slider("TNOC (°C)", 35.0, 50.0, plant_config["noct"], 0.5)
        temp_coeff = st.slider(
            "γ - Coef. Temperatura (%/°C)",
            -0.01,
            0.0,
            plant_config["temp_coeff"],
            0.0001,
            format="%.4f",
        )

        irrad_coeff = st.slider(
            "c - Coef. Irradiância",
            0.0,
            0.1,
            plant_config["irrad_coeff"],
            0.001,
            format="%.3f",
        )

    # ----------------------------------------------------------------------------------------------------------------
    # Perdas DC
    # ----------------------------------------------------------------------------------------------------------------
    if apply_dc_losses:
        # st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        st.markdown("#####  Configuração de Perdas DC")

        with st.container(border=True):
            use_dc_defaults = st.checkbox("Usar configuração padrão NBR", value=False)

            if use_dc_defaults:
                a0 = default_params.dc_loss_coeffs.a0
                a1 = default_params.dc_loss_coeffs.a1
                a2 = default_params.dc_loss_coeffs.a2

                st.metric("a₀ - Perdas Fixas", f"{a0:.3f}", f"{a0 * 100:.1f}%")
                st.metric("a₁ - Baixa Irradiância", f"{a1:.3f}", f"{a1 * 100:+.1f}%")
                st.metric("a₂ - Alta Irradiância", f"{a2:.3f}", f"{a2 * 100:.1f}%")
            else:
                a0 = st.slider(
                    "a₀ - Perdas Fixas",
                    default_params.dc_loss_coeffs.a0_min,
                    default_params.dc_loss_coeffs.a0_max,
                    default_params.dc_loss_coeffs.a0,
                    0.005,
                    format="%.3f",
                )
                a1 = st.slider(
                    "a₁ - Baixa Irradiância",
                    default_params.dc_loss_coeffs.a1_min,
                    default_params.dc_loss_coeffs.a1_max,
                    default_params.dc_loss_coeffs.a1,
                    0.005,
                    format="%.3f",
                )
                a2 = st.slider(
                    "a₂ - Alta Irradiância",
                    default_params.dc_loss_coeffs.a2_min,
                    default_params.dc_loss_coeffs.a2_max,
                    default_params.dc_loss_coeffs.a2,
                    0.005,
                    format="%.3f",
                )
    else:
        a0 = a1 = a2 = None

    # ---------------------------------------------------------------------------------------------------------------------
    # Parâmetros do inversor
    # ---------------------------------------------------------------------------------------------------------------------
    if use_nbr_efficiency:
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        st.markdown("#####  Parâmetros perda do Inversor")

        with st.container(border=True):
            use_inverter_defaults = st.checkbox("Usar parâmetros padrão Canadian Solar", value=False)
            if use_inverter_defaults:
                k0 = default_params.inverter_coeffs.k0
                k1 = default_params.inverter_coeffs.k1
                k2 = default_params.inverter_coeffs.k2

                st.metric("k₀", f"{k0:.4f}", "Perdas fixas")
                st.metric("k₁", f"{k1:.4f}", "Perdas lineares")
                st.metric("k₂", f"{k2:.4f}", "Perdas quadráticas")
            else:
                k0 = st.slider(
                    "k₀",
                    default_params.inverter_coeffs.k0_min,
                    default_params.inverter_coeffs.k0_max,
                    default_params.inverter_coeffs.k0,
                    0.0001,
                    format="%.4f",
                )
                k1 = st.slider(
                    "k₁",
                    default_params.inverter_coeffs.k1_min,
                    default_params.inverter_coeffs.k1_max,
                    default_params.inverter_coeffs.k1,
                    0.0001,
                    format="%.4f",
                )
                k2 = st.slider(
                    "k₂",
                    default_params.inverter_coeffs.k2_min,
                    default_params.inverter_coeffs.k2_max,
                    default_params.inverter_coeffs.k2,
                    0.0001,
                    format="%.4f",
                )
    else:
        k0 = k1 = k2 = None

    # ---------------------------------------------------------------------------------------------------------------------
    # Perdas AC
    # ---------------------------------------------------------------------------------------------------------------------
    if apply_ac_losses:
        st.markdown("#####  Configuração de Perdas AC")

        with st.container(border=True):
            use_ac_defaults = st.checkbox("Usar configuração padrão de perdas AC", value=True)

            if use_ac_defaults:
                ac_wiring = default_params.ac_loss_coeffs.wiring
                ac_transformer = default_params.ac_loss_coeffs.transformer
                ac_protection = default_params.ac_loss_coeffs.protection
                ac_monitoring = default_params.ac_loss_coeffs.monitoring
                ac_other = default_params.ac_loss_coeffs.other

                total_ac_loss = default_params.ac_loss_coeffs.ac_loss
                st.metric("Perdas AC Totais", f"{total_ac_loss:.1%}", f"{total_ac_loss * 100:.1f}%")

            else:
                ac_wiring = st.slider("Cabeamento AC (%)", 0.5, 3.0, default_params.ac_loss_coeffs.wiring * 100) / 100
                ac_transformer = (
                    st.slider("Transformador (%)", 0.0, 1.0, default_params.ac_loss_coeffs.transformer * 100) / 100
                )
                ac_protection = (
                    st.slider("Proteções (%)", 0.1, 1.0, default_params.ac_loss_coeffs.protection * 100) / 100
                )
                ac_monitoring = (
                    st.slider("Monitoramento (%)", 0.1, 0.5, default_params.ac_loss_coeffs.monitoring * 100) / 100
                )
                ac_other = st.slider("Outras perdas (%)", 0.0, 1.0, default_params.ac_loss_coeffs.other * 100) / 100
    else:
        ac_wiring = ac_transformer = ac_protection = ac_monitoring = ac_other = None


with right_col:
    with st.expander(" Ver Resumo Técnico dos Parâmetros"):
        summary_data = {
            "Parâmetro": [
                "Potência Nominal",
                "TNOC",
                "Coef. Temperatura",
                "Coef. Irradiância",
                "a₀ (Perdas Fixas)",
                "a₁ (Baixa Irrad.)",
                "a₂ (Alta Irrad.)",
                "k₀ (Inversor)",
                "k₁ (Inversor)",
                "k₂ (Inversor)",
                "Perdas AC Totais",
                "Método Eficiência",
            ],
            "Valor": [
                f"{default_params.capacity_kwp:.1f} kWp",
                f"{noct:.1f} °C",
                f"{temp_coeff:.4f} %/°C",
                f"{irrad_coeff:.3f}",
                f"{a0:.3f}",
                f"{a1:.3f}",
                f"{a2:.3f}",
                f"{k0:.4f}",
                f"{k1:.4f}",
                f"{k2:.4f}",
                f"{(ac_wiring + ac_transformer + ac_protection + ac_monitoring + ac_other):.1%}",
                "NBR 16274" if use_nbr_efficiency else "PV*SOL",
            ],
            "Norma": [
                "NBR 16274",
                "NBR 16274",
                "NBR 16274 G.1",
                "NBR 16274 E.1",
                "NBR 16274 F.1",
                "NBR 16274 F.1",
                "NBR 16274 F.1",
                "NBR 16274 E.2",
                "NBR 16274 E.2",
                "NBR 16274 E.2",
                "Estimado",
                "Configurável",
            ],
        }

        st.dataframe(pd.DataFrame(summary_data), width="stretch", hide_index=True)

    if st.button(" Executar Simulação NBR 16274", type="primary", width="stretch"):
        try:
            params = create_system_parameters(
                capacity_kwp=default_params.capacity_kwp,
                noct=noct,
                temp_coeff=temp_coeff,
                irrad_coeff=irrad_coeff,
                dc_coeffs=(a0, a1, a2),
                inverter_coeffs=(k0, k1, k2),
                ac_losses=(ac_wiring, ac_transformer, ac_protection, ac_monitoring, ac_other)
                if apply_ac_losses
                else None,
            )
            with st.spinner("Executando simulação NBR 16274..."):
                results = run_pv_simulation(
                    df_data=df_data,
                    params=params,
                    apply_dc_losses=apply_dc_losses,
                    apply_ac_losses=apply_ac_losses,
                    use_nbr_efficiency=use_nbr_efficiency,
                )

            st.success("✅ Simulação concluída com sucesso!")

        except Exception as e:
            st.error(f"❌ Erro na simulação: {str(e)}")
            st.info("Verifique os parâmetros inseridos e tente novamente.")
    else:
        st.info("👆 Configure os parâmetros e clique em 'Executar Simulação' para ver os resultados")

    if "results" in locals():
        st.write(" ")
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        st.markdown("#### Resultados da Simulação")
        st.write(" ")

        # display_simulation_results(results)

        with st.expander(" Ver Dados Detalhados da Simulação"):
            st.dataframe(
                results[
                    [
                        "gti",
                        "air_temp",
                        "cell_temp",
                        "dc_power_kw",
                        "cpdc",
                        "dc_power_adj_kw",
                        "inv_efficiency",
                        "ac_power_kw_est",
                    ]
                ].round(3),
                width="stretch",
            )
        df_pred = pd.DataFrame(index=results.index)
        df_pred["y_true"] = results["energy"]
        df_pred["y_pred"] = results["ac_power_kw_est"]
        df_pred = df_pred.between_time("06:00", "18:00").copy()

        # df_pred = df_pred.dropna().copy()
        # df_pred = df_pred[df_pred["y_true"].notnull() & df_pred["y_pred"].notnull()]

        if df_pred["y_true"].isnull().any():
            null_values = df_pred["y_true"].isnull().sum()
            st.warning(f"Dados de produção contêm {null_values} valores nulos. Métricas podem ser afetadas.")

        if df_pred["y_pred"].isnull().any():
            null_values = df_pred["y_pred"].isnull().sum()
            st.warning(f"Dados previstos contêm {null_values} valores nulos. Métricas podem ser afetadas.")

        metrics = calculate_forecast_accuracy(df_pred["y_true"], df_pred["y_pred"], "PV Model NBR 16274")

        # -------------------------------------------------------------------------------------------------------------
        daily_pv_curve_analyzer(df_pred, "y_true", "y_pred")
        plot_metrics(df_pred, metrics)

        # -------------------------------------------------------------------------------------------------------------

        csv = results.to_csv()
        st.download_button(
            label="📥 Download Resultados CSV",
            data=csv,
            file_name=f"simulacao_pv_{selected_plant}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
        )
