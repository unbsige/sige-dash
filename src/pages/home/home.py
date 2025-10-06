from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from src.data.solar_plants_manager import SolarDataManager


def st_metrics_row(manager: SolarDataManager):
    metrics = manager.get_summary_metrics()

    plants_with_device = len(manager.plants_data) - len(manager.get_plants_without_device_id())
    plants_with_creds = len(manager.plants_data) - len(manager.get_plants_without_credentials())

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Usinas", metrics.get("total_plants", 0))
    with col2:
        st.metric("Potência Total", f"{metrics.get('total_power_kwp', 0):,.0f} kWp")
    with col3:
        st.metric("Geração Anual", f"{metrics.get('total_generation_kwh', 0) / 1000:,.1f} MWh")
    with col4:
        st.metric("Campus", metrics.get("campus_count", 0))


def st_plant_selector(manager: SolarDataManager, key="plant_selector"):
    options = manager.get_selectbox_options()
    plant_options = options.get("plants", {})

    selected = st.selectbox(
        "Selecione uma Usina:",
        options=[""] + list(plant_options.keys()),
        key=key,
    )

    plant_data = plant_options.get(selected) if selected else None
    return selected, plant_data


def st_advanced_filters(manager: SolarDataManager):
    options = manager.get_selectbox_options()
    st.sidebar.header("Filtros Avançados")

    filters = {}
    filters["Campus"] = st.sidebar.multiselect("Campus:", options.get("campus", []))
    filters["Status"] = st.sidebar.multiselect("Status:", options.get("status", []))
    filters["Manufacturers"] = st.sidebar.multiselect("Fabricante:", options.get("manufacturers", []))

    st.sidebar.subheader("Faixa de Potência")
    df = manager.get_dataframe()

    if not df.empty:
        max_power = df["Potência (kWp)"].max()
        power_range = st.sidebar.slider(
            "Potência (kWp):", min_value=0.0, max_value=float(max_power), value=(0.0, float(max_power)), step=5.0
        )

        power_filtered = df[(df["Potência (kWp)"] >= power_range[0]) & (df["Potência (kWp)"] <= power_range[1])]
        filters["power_filtered_codes"] = power_filtered["Código"].tolist()

    return filters


def st_plant_details_card(plant_data):
    if not plant_data:
        st.info("Selecione uma usina acima para ver os detalhes")
        return

    plant_name = plant_data.get("acronym", plant_data.get("code", "N/A"))

    st.subheader(f"{plant_name}")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Potência", f"{plant_data.get('power_kwp', 0)} kWp")
        st.write(f"**Campus:** {plant_data.get('campus', 'N/A')}")
        st.write(f"**Edifício:** {plant_data.get('building', 'N/A')}")

    with col2:
        generation = plant_data.get("annual_generation_kwh", 0)
        st.metric("Geração Anual", f"{generation / 1000:,.1f} MWh")
        st.write(f"**Instalação:** {plant_data.get('installation_date', 'N/A')}")

        coords = plant_data.get("coordinates", {})
        if coords.get("latitude") and coords.get("longitude"):
            st.write(f"**Localização:** {coords['latitude']:.3f}, {coords['longitude']:.3f}")

    with col3:
        status = plant_data.get("status", "N/A")
        status_color = "normal" if status == "Ativa" else "off"
        st.metric("Status", status, delta_color=status_color)

        cred_status = "Sim" if plant_data.get("credentials", {}).get("username", "").strip() else "Não"
        device_status = "Sim" if plant_data.get("device", {}).get("device_id", "").strip() else "Não"
        st.write(f"**Credenciais:** {cred_status}")
        st.write(f"**Device ID:** {device_status}")

    with st.expander("Detalhes Técnicos"):
        tech_specs = plant_data.get("technical_specs", {})
        device = plant_data.get("device", {})

        col_tech1, col_tech2 = st.columns(2)

        with col_tech1:
            st.write("**Especificações dos Painéis:**")
            st.write(f"• Quantidade: {tech_specs.get('panel_count', 0)} painéis")
            st.write(f"• Potência: {tech_specs.get('panel_power_wp', 0)} Wp cada")
            st.write(f"• Strings: {tech_specs.get('string_count', 0)}")
            if tech_specs.get("inverter_model"):
                st.write(f"• Inversor: {tech_specs.get('inverter_model')}")

        with col_tech2:
            st.write("**Dispositivo de Monitoramento:**")
            st.write(f"• Fabricante: {device.get('manufacturer', 'N/A')}")
            st.write(f"• Modelo: {device.get('model', 'N/A')}")
            st.write(f"• Device ID: {device.get('device_id', 'N/A')}")

            creds = plant_data.get("credentials", {})
            username = creds.get("username", "")
            if username:
                st.write(f"• Usuário: {username}")


def create_installation_timeline_chart(manager: SolarDataManager):
    df = manager.get_dataframe()

    if df.empty or df["Data Instalação"].isna().all():
        return None

    df_timeline = df[df["Data Instalação"].notna()].copy()

    if df_timeline.empty:
        return None

    try:
        df_timeline["Ano"] = pd.to_datetime(df_timeline["Data Instalação"]).dt.year

        timeline_data = (
            df_timeline.groupby(["Ano", "Campus"]).agg({"Potência (kWp)": "sum", "Código": "count"}).reset_index()
        )

        timeline_data.rename(columns={"Código": "Quantidade"}, inplace=True)

        fig = px.bar(
            timeline_data,
            x="Ano",
            y="Potência (kWp)",
            color="Campus",
            title="Timeline de Instalações por Ano",
            hover_data=["Quantidade"],
            text="Potência (kWp)",
        )

        fig.update_traces(texttemplate="%{text:.0f} kWp", textposition="outside")
        fig.update_layout(height=400)

        return fig

    except Exception as e:
        st.error(f"Erro ao processar timeline: {e}")
        return None


def render_summary_section(manager: SolarDataManager):
    st.markdown("### Resumo do Sistema")

    st_metrics_row(manager)

    st.markdown("---")


def render_plant_analysis_section(manager: SolarDataManager):
    st.markdown("### Análise Individual")

    col1, _ = st.columns([1, 2])

    with col1:
        selected, plant_data = st_plant_selector(manager)

        if st.button("Recarregar Dados", width="stretch"):
            manager.reload_data()
            st.rerun()

    if plant_data:
        st_plant_details_card(plant_data)

    st.markdown("---")


def render_data_section(manager: SolarDataManager, filters):
    st.markdown("### Dados das Usinas")

    if any(filters.values()):
        filtered_df = manager.apply_filters(filters)
    else:
        filtered_df = manager.get_dataframe()

    if not filtered_df.empty:
        display_columns = [
            "Nome",
            "Campus",
            "Status",
            "Potência (kWp)",
            "Geração Anual (kWh)",
            "Qtd Painéis",
        ]

        available_columns = [col for col in display_columns if col in filtered_df.columns]
        st.dataframe(filtered_df[available_columns], width="stretch", height=400, hide_index=True)

        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"usinas_unb_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
        )
    else:
        st.warning("Nenhuma usina encontrada com os filtros aplicados")

    st.markdown("---")


def render_visualizations_section(manager: SolarDataManager):
    st.markdown("### Visualizações")

    tab1, tab2, tab3 = st.tabs(["Por Campus", "Mapa", "Timeline"])

    with tab1:
        fig1 = manager.create_power_by_campus_chart()
        if fig1:
            st.plotly_chart(fig1, width="stretch")
        else:
            st.info("Dados de campus não disponíveis")

    with tab2:
        fig_map = manager.create_map_chart()
        if fig_map:
            st.plotly_chart(fig_map, width="stretch")
        else:
            st.info("Dados de coordenadas não disponíveis para o mapa")

    with tab3:
        fig_timeline = create_installation_timeline_chart(manager)
        if fig_timeline:
            st.plotly_chart(fig_timeline, width="stretch")
        else:
            st.info("Dados de instalação não disponíveis para timeline")


def render_homepage():
    st.set_page_config(
        page_title="Dashboard Solar UnB",
        # page_icon="☀️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown(
        """
        <style>
        .main > div {
            padding-top: 2rem;
        }
        .stMetric {
            background-color: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        </style>
    """,
        unsafe_allow_html=True,
    )

    st.title("Usinas Fotovoltaicas UnB")

    manager = SolarDataManager("data/solar_plants.json")

    if not manager.plants_data:
        st.error("❌ Erro ao carregar dados das usinas.")
        st.info("Verifique se o arquivo 'data/solar_plants.json' existe e está formatado corretamente.")
        return

    filters = st_advanced_filters(manager)

    with st.sidebar:
        st.markdown("---")

        if st.button("Validar Dados"):
            issues = manager.validate_data_integrity()
            if issues:
                st.error("Problemas encontrados:")
                for issue in issues[:3]:
                    st.error(f"• {issue}")
            else:
                st.success("Dados íntegros!")

    render_summary_section(manager)
    render_plant_analysis_section(manager)
    render_data_section(manager, filters)
    render_visualizations_section(manager)

    st.markdown("---")
    st.markdown(
        f"""
        <div style='text-align: center; color: #666; font-size: 0.8rem;'>
            Dashboard atualizado em {datetime.now().strftime("%d/%m/%Y às %H:%M")} | 
            Dados: {len(manager.plants_data)} usinas
        </div>
        """,
        unsafe_allow_html=True,
    )
