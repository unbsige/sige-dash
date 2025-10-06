import datetime
import warnings

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from pages.physical_model.components.analyzer import daily_pv_curve_analyzer
from pages.physical_model.components.charts import create_preview_chart
from pages.physical_model.components.results import plot_metrics
from src.config.settings import PLANTS_CONFIG
from src.config.styles import ThemeManager, render_col_divider
from src.data.data_loader import get_available_plants, load_historical_data
from src.metrics import calculate_forecast_accuracy
from src.models.physical.params import PVSystemParameters, create_system_parameters
from src.models.physical.run import run_pv_simulation
from src.pages.physical_model.components.simulator_results import display_simulation_results

warnings.filterwarnings("ignore")

st.set_page_config(
    page_title="Simulador PV NBR 16274",
    page_icon="☀️",
    layout="wide",
)


def initialize_session_state():
    """Inicializa variáveis de estado da sessão"""
    if "simulation_executed" not in st.session_state:
        st.session_state.simulation_executed = False

    if "simulation_results" not in st.session_state:
        st.session_state.simulation_results = None

    if "df_pred" not in st.session_state:
        st.session_state.df_pred = None

    if "metrics" not in st.session_state:
        st.session_state.metrics = None

    if "selected_plant_key" not in st.session_state:
        st.session_state.selected_plant_key = None


def render_header():
    st.markdown(
        """
        <div style="
            background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
            padding: 20px 25px;
            border-radius: 8px;
            margin-bottom: 30px;
            color: white;
            box-shadow: 0 2px 8px rgba(33, 150, 243, 0.2);
        ">
            <h1 style="margin: 0; font-size: 1.8rem; font-weight: 500;">
                Simulador de Previsão Fotovoltaica - NBR 16274:2014
            </h1>
            <p style="margin: 5px 0 0 0; opacity: 0.9; font-size: 1rem;">
                Ferramenta para simulação conforme a norma brasileira NBR 16274:2014
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_plant_selection():
    st.markdown("### Seleção da Planta Fotovoltaica")

    available_plants = get_available_plants()
    if not available_plants:
        st.error("Nenhuma planta com credenciais configuradas encontrada")
        st.stop()

    col1, col2 = st.columns([1, 2])

    with col1:
        plant_options = {key: config["name"] for key, config in available_plants.items()}
        selected_plant_key = st.selectbox(
            "Planta",
            options=[None] + list(plant_options.keys()),
            format_func=lambda x: "Selecione uma planta..." if x is None else plant_options[x],
            index=0,
            key="plant_selector",
        )

        if selected_plant_key is None:
            st.info("Por favor, selecione uma planta para continuar.")
            st.stop()

        if st.session_state.selected_plant_key != selected_plant_key:
            st.session_state.selected_plant_key = selected_plant_key
            st.session_state.simulation_executed = False
            st.session_state.simulation_results = None

        plant_config = available_plants[selected_plant_key]

        st.info(f"""
        **{plant_config["name"]}**
        - Localização: {plant_config["location"]}
        - Capacidade: {plant_config["capacity_kwp"]} kWp
        - Latitude: {plant_config["latitude"]:.3f}°
        - Longitude: {plant_config["longitude"]:.3f}°
        """)

    with col2:
        subcol1, subcol2 = st.columns(2)

        with subcol1:
            try:
                photo_path = "assets/campus_fcte_uac.jpeg"
                st.image(photo_path, caption=f"Vista da {plant_config['acronym']}")
            except:
                st.info(f"📷 Foto da {plant_config['acronym']} não disponível")

        with subcol2:
            if plant_config.get("latitude") and plant_config.get("longitude"):
                lat = plant_config["latitude"]
                lon = plant_config["longitude"]

                fig_map = go.Figure(
                    go.Scattermapbox(
                        lat=[lat],
                        lon=[lon],
                        mode="markers",
                        marker=go.scattermapbox.Marker(size=10, color="#2196F3"),
                        hoverinfo="text",
                    )
                )

                fig_map.update_layout(
                    mapbox_style="open-street-map",
                    mapbox=dict(center=go.layout.mapbox.Center(lat=lat, lon=lon), zoom=16),
                    showlegend=False,
                    height=200,
                    margin={"r": 0, "t": 0, "l": 0, "b": 0},
                )

                st.plotly_chart(fig_map, width="stretch", config={"displayModeBar": False})
            else:
                st.warning("⚠️ Coordenadas não disponíveis")

    return selected_plant_key, plant_config


def render_data_selection_tab(selected_plant_key):
    df_power = load_historical_data(selected_plant_key, freq="5min", with_radiation=True)
    if df_power.empty:
        st.info("Nenhum dado histórico encontrado. Verifique se o arquivo CSV existe.")
        st.stop()

    st.markdown("### Período de Análise")

    if df_power.index.tz is not None:
        min_date = df_power.index.tz_convert(None).min().date()
        max_date = df_power.index.tz_convert(None).max().date()
    else:
        min_date = df_power.index.min().date()
        max_date = df_power.index.max().date()

    st.write(f"min: {min_date}, max: {max_date}")
    col1, col2, col3 = st.columns([1, 1, 1])

    today = max_date
    # Definir intervalo inicial: últimos 30 dias ou mês corrente
    last_30_days_start = today - datetime.timedelta(days=29)
    month_start = today.replace(day=1)

    # Escolher intervalo padrão: se houver pelo menos 30 dias de dados, usar últimos 30 dias, senão mês corrente
    if (today - min_date).days >= 29:
        default_start = last_30_days_start
    else:
        default_start = month_start if month_start >= min_date else min_date

    with col1:
        start_date = st.date_input(
            "Data inicial",
            value=default_start,
            min_value=min_date,
            max_value=max_date,
            format="DD/MM/YYYY",
            key="start_date_selector",
        )

    with col2:
        end_date = st.date_input(
            "Data final",
            value=today,
            min_value=min_date,
            max_value=max_date,
            format="DD/MM/YYYY",
            key="end_date_selector",
        )

    with col3:
        if start_date > end_date:
            st.error("Data inicial deve ser anterior à final")
            return pd.DataFrame()

        period_days = (end_date - start_date).days + 1
        st.metric("Período", f"{period_days} dias")

    st.write("---")
    st.write(f"Start: {start_date} | End: {end_date}")
    st.write("---")

    if df_power.index.tz is not None:
        start_datetime = pd.Timestamp(start_date).tz_localize(df_power.index.tz)
        end_datetime = pd.Timestamp(end_date).tz_localize(df_power.index.tz) + pd.Timedelta(days=1, seconds=-1)
    else:
        start_datetime = pd.Timestamp(start_date)
        end_datetime = pd.Timestamp(end_date) + pd.Timedelta(days=1, seconds=-1)

    df_filtered = df_power.loc[start_datetime:end_datetime].copy()

    if df_filtered.empty:
        st.warning("Nenhum dado encontrado para o período selecionado")
        return df_filtered

    st.markdown("**Preview dos dados selecionados:**")
    fig_preview = create_simple_preview_chart(df_filtered, start_date, end_date)
    st.plotly_chart(fig_preview, width="stretch", config={"displayModeBar": False})

    return df_filtered


def create_simple_preview_chart(df_filtered, start_date, end_date):
    power_column = None
    for col in df_filtered.columns:
        if "power" in col.lower() or "potencia" in col.lower():
            power_column = col
            break

    if power_column is None:
        power_column = df_filtered.columns[0]

    if len(df_filtered) > 1000:
        data = df_filtered[power_column].resample("H").mean()
    else:
        data = df_filtered[power_column]

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data.values,
            mode="lines",
            line=dict(color="#2196F3", width=2),
            hovertemplate="%{x}<br>%{y:.1f} kW<extra></extra>",
            showlegend=False,
        )
    )

    fig.update_layout(
        xaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.1)", title=""),
        yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.1)", title="Potência (kW)"),
        plot_bgcolor="white",
        paper_bgcolor="rgba(0,0,0,0)",
        height=300,
        margin=dict(t=20, b=40, l=50, r=20),
        font=dict(size=12),
    )

    return fig


def render_parameters_tab(plant_config):
    st.markdown("### Configuração de Parâmetros")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("#### Configurações Gerais")
        apply_dc_losses = st.checkbox("Aplicar perdas DC", value=True, key="apply_dc")
        apply_ac_losses = st.checkbox("Aplicar perdas AC", value=True, key="apply_ac")
        use_nbr_efficiency = st.checkbox("Usar eficiência NBR 16274", value=True, key="use_nbr")

    with col2:
        st.markdown("#### Parâmetros do Sistema")

        default_params = PVSystemParameters(capacity_kwp=plant_config["capacity_kwp"])

        noct = st.slider("TNOC (°C)", 35.0, 50.0, plant_config["noct"], 0.5, key="noct_slider")
        temp_coeff = st.slider(
            "γ - Coef. Temperatura (%/°C)",
            -0.01,
            0.0,
            plant_config["temp_coeff"],
            0.0001,
            format="%.4f",
            key="temp_coeff_slider",
        )
        irrad_coeff = st.slider(
            "c - Coef. Irradiância",
            0.0,
            0.1,
            plant_config["irrad_coeff"],
            0.001,
            format="%.3f",
            key="irrad_coeff_slider",
        )

    if apply_dc_losses:
        st.markdown("---")
        st.markdown("#### Configuração de Perdas DC")

        col1, col2 = st.columns([1, 1])

        with col1:
            use_dc_defaults = st.checkbox("Usar configuração padrão NBR", value=False, key="dc_defaults")

        with col2:
            if use_dc_defaults:
                a0 = default_params.dc_loss_coeffs.a0
                a1 = default_params.dc_loss_coeffs.a1
                a2 = default_params.dc_loss_coeffs.a2

                st.metric("a₀ - Perdas Fixas", f"{a0:.3f}")
                st.metric("a₁ - Baixa Irradiância", f"{a1:.3f}")
                st.metric("a₂ - Alta Irradiância", f"{a2:.3f}")
            else:
                a0 = st.slider(
                    "a₀ - Perdas Fixas",
                    default_params.dc_loss_coeffs.a0_min,
                    default_params.dc_loss_coeffs.a0_max,
                    default_params.dc_loss_coeffs.a0,
                    0.005,
                    format="%.3f",
                    key="a0_slider",
                )

                a1 = st.slider(
                    "a₁ - Baixa Irradiância",
                    default_params.dc_loss_coeffs.a1_min,
                    default_params.dc_loss_coeffs.a1_max,
                    default_params.dc_loss_coeffs.a1,
                    0.005,
                    format="%.3f",
                    key="a1_slider",
                )

                a2 = st.slider(
                    "a₂ - Alta Irradiância",
                    default_params.dc_loss_coeffs.a2_min,
                    default_params.dc_loss_coeffs.a2_max,
                    default_params.dc_loss_coeffs.a2,
                    0.005,
                    format="%.3f",
                    key="a2_slider",
                )
    else:
        a0 = a1 = a2 = None

    if use_nbr_efficiency:
        st.markdown("---")
        st.markdown("#### Parâmetros do Inversor")

        col1, col2 = st.columns([1, 1])

        with col1:
            use_inverter_defaults = st.checkbox(
                "Usar parâmetros padrão Canadian Solar", value=False, key="inv_defaults"
            )

        with col2:
            if use_inverter_defaults:
                k0 = default_params.inverter_coeffs.k0
                k1 = default_params.inverter_coeffs.k1
                k2 = default_params.inverter_coeffs.k2

                st.metric("k₀", f"{k0:.4f}")
                st.metric("k₁", f"{k1:.4f}")
                st.metric("k₂", f"{k2:.4f}")
            else:
                k0 = st.slider(
                    "k₀",
                    default_params.inverter_coeffs.k0_min,
                    default_params.inverter_coeffs.k0_max,
                    default_params.inverter_coeffs.k0,
                    0.0001,
                    format="%.4f",
                    key="k0_slider",
                )

                k1 = st.slider(
                    "k₁",
                    default_params.inverter_coeffs.k1_min,
                    default_params.inverter_coeffs.k1_max,
                    default_params.inverter_coeffs.k1,
                    0.0001,
                    format="%.4f",
                    key="k1_slider",
                )

                k2 = st.slider(
                    "k₂",
                    default_params.inverter_coeffs.k2_min,
                    default_params.inverter_coeffs.k2_max,
                    default_params.inverter_coeffs.k2,
                    0.0001,
                    format="%.4f",
                    key="k2_slider",
                )
    else:
        k0 = k1 = k2 = None

    if apply_ac_losses:
        st.markdown("---")
        st.markdown("#### Configuração de Perdas AC")

        col1, col2 = st.columns([1, 1])

        with col1:
            use_ac_defaults = st.checkbox("Usar configuração padrão de perdas AC", value=True, key="ac_defaults")

        with col2:
            if use_ac_defaults:
                ac_wiring = default_params.ac_loss_coeffs.wiring
                ac_transformer = default_params.ac_loss_coeffs.transformer
                ac_protection = default_params.ac_loss_coeffs.protection
                ac_monitoring = default_params.ac_loss_coeffs.monitoring
                ac_other = default_params.ac_loss_coeffs.other

                total_ac_loss = default_params.ac_loss_coeffs.ac_loss
                st.metric("Perdas AC Totais", f"{total_ac_loss:.1%}")
            else:
                ac_wiring = (
                    st.slider(
                        "Cabeamento AC (%)", 0.5, 3.0, default_params.ac_loss_coeffs.wiring * 100, key="ac_wiring"
                    )
                    / 100
                )
                ac_transformer = (
                    st.slider(
                        "Transformador (%)",
                        0.0,
                        1.0,
                        default_params.ac_loss_coeffs.transformer * 100,
                        key="ac_transformer",
                    )
                    / 100
                )
                ac_protection = (
                    st.slider(
                        "Proteções (%)", 0.1, 1.0, default_params.ac_loss_coeffs.protection * 100, key="ac_protection"
                    )
                    / 100
                )
                ac_monitoring = (
                    st.slider(
                        "Monitoramento (%)",
                        0.1,
                        0.5,
                        default_params.ac_loss_coeffs.monitoring * 100,
                        key="ac_monitoring",
                    )
                    / 100
                )
                ac_other = (
                    st.slider("Outras perdas (%)", 0.0, 1.0, default_params.ac_loss_coeffs.other * 100, key="ac_other")
                    / 100
                )
    else:
        ac_wiring = ac_transformer = ac_protection = ac_monitoring = ac_other = None

    return {
        "apply_dc_losses": apply_dc_losses,
        "apply_ac_losses": apply_ac_losses,
        "use_nbr_efficiency": use_nbr_efficiency,
        "noct": noct,
        "temp_coeff": temp_coeff,
        "irrad_coeff": irrad_coeff,
        "dc_coeffs": (a0, a1, a2),
        "inverter_coeffs": (k0, k1, k2),
        "ac_losses": (ac_wiring, ac_transformer, ac_protection, ac_monitoring, ac_other),
        "default_params": default_params,
    }


def render_simulation_tab(df_filtered, plant_config, params_config):
    """Renderiza tab de simulação"""

    st.markdown("### Executar Simulação")

    col1, col2 = st.columns([2, 1])

    with col1:
        with st.expander("Resumo Técnico dos Parâmetros"):
            summary_data = {
                "Parâmetro": [
                    "Potência Nominal",
                    "TNOC",
                    "Coef. Temperatura",
                    "Coef. Irradiância",
                    "Perdas DC",
                    "Perdas Inversor",
                    "Perdas AC",
                ],
                "Valor": [
                    f"{params_config['default_params'].capacity_kwp:.1f} kWp",
                    f"{params_config['noct']:.1f} °C",
                    f"{params_config['temp_coeff']:.4f} %/°C",
                    f"{params_config['irrad_coeff']:.3f}",
                    "Aplicadas" if params_config["apply_dc_losses"] else "Não aplicadas",
                    "NBR 16274" if params_config["use_nbr_efficiency"] else "PV*SOL",
                    "Aplicadas" if params_config["apply_ac_losses"] else "Não aplicadas",
                ],
            }

            st.dataframe(pd.DataFrame(summary_data), hide_index=True, width="stretch")

    with col2:
        # Botão de simulação
        if st.button("🔄 Executar Simulação NBR 16274", type="primary", width="stretch"):
            try:
                params = create_system_parameters(
                    capacity_kwp=params_config["default_params"].capacity_kwp,
                    noct=params_config["noct"],
                    temp_coeff=params_config["temp_coeff"],
                    irrad_coeff=params_config["irrad_coeff"],
                    dc_coeffs=params_config["dc_coeffs"],
                    inverter_coeffs=params_config["inverter_coeffs"],
                    ac_losses=params_config["ac_losses"] if params_config["apply_ac_losses"] else None,
                )

                with st.spinner("Executando simulação NBR 16274..."):
                    results = run_pv_simulation(
                        df_data=df_filtered,
                        params=params,
                        apply_dc_losses=params_config["apply_dc_losses"],
                        apply_ac_losses=params_config["apply_ac_losses"],
                        use_nbr_efficiency=params_config["use_nbr_efficiency"],
                    )

                df_pred = pd.DataFrame(index=results.index)
                df_pred["y_true"] = results["pv_power"]
                df_pred["y_pred"] = results["ac_power_kw_est"]
                df_pred = df_pred.between_time("06:00", "18:00").dropna()

                metrics = calculate_forecast_accuracy(df_pred["y_true"], df_pred["y_pred"], "PV Model NBR 16274")

                st.session_state.simulation_results = results
                st.session_state.df_pred = df_pred
                st.session_state.metrics = metrics
                st.session_state.simulation_executed = True

                st.success("✅ Simulação concluída com sucesso!")
                st.info("👆 Vá para a aba 'Resultados' para visualizar os resultados")

            except Exception as e:
                st.error(f"❌ Erro na simulação: {str(e)}")
                st.info("Verifique os parâmetros inseridos e tente novamente.")


def render_results_tab():
    if not st.session_state.simulation_executed or st.session_state.simulation_results is None:
        st.info("Execute uma simulação primeiro para visualizar os resultados.")
        return

    st.markdown("### Resultados da Simulação")

    display_simulation_results(
        st.session_state.simulation_results,
        st.session_state.df_pred,
        st.session_state.metrics,
        st.session_state.selected_plant_key,
    )


# --------------------------------------------------------------------------------------
# Inicializar
# --------------------------------------------------------------------------------------


initialize_session_state()
render_header()

selected_plant_key, plant_config = render_plant_selection()

tab1, tab2, tab3, tab4 = st.tabs(["📊 Dados", "⚙️ Parâmetros", "🔄 Simulação", "📈 Resultados"])
with tab1:
    df_filtered = render_data_selection_tab(selected_plant_key)

with tab2:
    params_config = render_parameters_tab(plant_config)

with tab3:
    if "df_filtered" in locals():
        render_simulation_tab(df_filtered, plant_config, params_config)
    else:
        st.info("Selecione os dados na aba 'Dados' primeiro.")

with tab4:
    render_results_tab()
