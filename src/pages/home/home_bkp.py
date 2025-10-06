from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.data.solar_plants_manager import SolarDataManager


class UnBSolarHomepage:
    def __init__(self, json_file_path: str = "data/solar_plants.json"):
        self.manager = SolarDataManager(json_file_path)

    def render_hero_section(self):
        st.markdown(
            """
            <div style="
            background: linear-gradient(90deg, #1976D2 0%, #2E7D32 100%);
            padding: 10px 8px;
            border-radius: 6px;
            margin-bottom: 8px;
            color: #fff;
            box-shadow: 0 1px 3px rgba(33, 150, 243, 0.095);
            ">
            <div style="text-align: center;">
                <span style="font-size: 1.8rem; font-weight: 600;">
                MEPA - Monitoramento Solar UnB
                </span>
                <div style="font-size: 0.9rem; font-weight: 400; opacity: 0.8;">
                Usinas Fotovoltaicas • Dados em tempo real
                </div>
            </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    def calculate_system_overview(self):
        metrics = self.manager.get_summary_metrics()

        environmental = self.manager.environmental_impact or {}
        total_capacity = metrics.get("total_power_kwp", 0)
        total_generation = metrics.get("total_generation_kwh", 0)

        estimated_annual_savings = total_generation * 0.65
        co2_avoided = environmental.get("annual_co2_reduction_tons", total_generation * 0.0817 / 1000)
        trees_equivalent = environmental.get("equivalent_trees_planted", co2_avoided * 45.45)  # ~22kg CO2/árvore

        return {
            "total_capacity": total_capacity,
            "total_plants": metrics.get("total_plants", 0),
            "active_plants": metrics.get("active_plants", 0),
            "total_generation": total_generation,
            "estimated_annual_savings": estimated_annual_savings,
            "co2_avoided": co2_avoided,
            "trees_equivalent": trees_equivalent,
            "campus_count": metrics.get("campus_count", 0),
            "plants_with_credentials": metrics.get("plants_with_credentials", 0),
            "total_panels": metrics.get("total_panels", 0),
        }

    def render_system_metrics(self):
        overview = self.calculate_system_overview()
        st.markdown("#### 📊 Visão Geral do Sistema")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(
                f"""
                <div style="
                    background: white;
                    border: 1px solid #E0E0E0;
                    border-left: 4px solid #4CAF50;
                    border-radius: 8px;
                    padding: 20px;
                    text-align: center;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                ">
                    <div style="color: #4CAF50; font-size: 1.5rem; margin-bottom: 8px;">🏭</div>
                    <div style="color: #388E3C; font-size: 1.8rem; font-weight: 600;">{overview["active_plants"]}</div>
                    <div style="color: #777; font-size: 0.9rem;">Plantas Ativas</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col2:
            st.markdown(
                f"""
                <div style="
                    background: white;
                    border: 1px solid #E0E0E0;
                    border-left: 4px solid #2196F3;
                    border-radius: 8px;
                    padding: 20px;
                    text-align: center;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                ">
                    <div style="color: #2196F3; font-size: 1.5rem; margin-bottom: 8px;">⚡</div>
                    <div style="color: #1976D2; font-size: 1.8rem; font-weight: 600;">{overview["total_capacity"]:.0f}</div>
                    <div style="color: #777; font-size: 0.9rem;">kWp Instalados</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col3:
            st.markdown(
                f"""
                <div style="
                    background: white;
                    border: 1px solid #E0E0E0;
                    border-left: 4px solid #FF9800;
                    border-radius: 8px;
                    padding: 20px;
                    text-align: center;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                ">
                    <div style="color: #FF9800; font-size: 1.5rem; margin-bottom: 8px;">🔋</div>
                    <div style="color: #F57C00; font-size: 1.8rem; font-weight: 600;">{overview["total_generation"] / 1000:.0f}</div>
                    <div style="color: #777; font-size: 0.9rem;">MWh/ano</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col4:
            st.markdown(
                f"""
                <div style="
                    background: white;
                    border: 1px solid #E0E0E0;
                    border-left: 4px solid #9C27B0;
                    border-radius: 8px;
                    padding: 20px;
                    text-align: center;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                ">
                    <div style="color: #9C27B0; font-size: 1.5rem; margin-bottom: 8px;">💰</div>
                    <div style="color: #7B1FA2; font-size: 1.8rem; font-weight: 600;">R$ {overview["estimated_annual_savings"] / 1000:.0f}k</div>
                    <div style="color: #777; font-size: 0.9rem;">Economia anual</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    def render_campus_overview(self):
        st.markdown("---")
        st.markdown("#### 🏛️ Campus da UnB")

        campus_analysis = self.manager.get_campus_analysis()
        cols = st.columns(len(campus_analysis))
        for i, (campus_name, campus_data) in enumerate(campus_analysis.items()):
            with cols[i]:
                campus_icons = {"Darcy Ribeiro": "🏛️", "Gama": "🔬", "Ceilândia": "🏥", "Planaltina": "🌾"}

                icon = campus_icons.get(campus_name, "🏢")

                st.markdown(
                    f"""
                    <div style="
                        background: white;
                        border: 1px solid #E0E0E0;
                        border-radius: 8px;
                        padding: 20px;
                        text-align: center;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                        margin: 10px 0;
                    ">
                        <div style="font-size: 2rem; margin-bottom: 10px;">{icon}</div>
                        <h4 style="color: #2196F3; margin: 0 0 10px 0;">{campus_name}</h4>
                        <div style="color: #777; margin: 5px 0;">
                            <strong>{campus_data["plant_count"]}</strong> usinas
                        </div>
                        <div style="color: #777; margin: 5px 0;">
                            <strong>{campus_data["total_power"]:.0f}</strong> kWp
                        </div>
                        <div style="color: #777; margin: 5px 0;">
                            <strong>{campus_data["total_generation"] / 1000:.0f}</strong> MWh/ano
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    def render_plants_overview(self):
        """Renderiza visão detalhada das plantas"""
        st.markdown("---")
        st.markdown("#### 🏭 Principais Usinas do Sistema")

        df = self.manager.get_dataframe()
        top_plants = df.nlargest(6, "Potência (kWp)")

        for i in range(0, len(top_plants), 2):
            col1, col2 = st.columns(2)

            if i < len(top_plants):
                plant_row = top_plants.iloc[i]
                self._render_plant_card(col1, plant_row)

            if i + 1 < len(top_plants):
                plant_row = top_plants.iloc[i + 1]
                self._render_plant_card(col2, plant_row)

    def _render_plant_card(self, container, plant_row):
        with container:
            icon = "📚"
            config_status = "🟢" if plant_row["Tem Device ID"] else "🟡"

            st.markdown(
                f"""
                <div style="
                    background: white;
                    border: 1px solid #E0E0E0;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 10px 0;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                    height: 200px;
                ">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <h4 style="color: #2196F3; margin: 0; font-size: 1.1rem;">{icon} {plant_row["Nome"]}</h4>
                        <span style="font-size: 1.2rem;" title="Status de configuração">{config_status}</span>
                    </div>
                    <p style="color: #777; margin: 5px 0; font-size: 0.9rem;"><strong>Campus:</strong> {plant_row["Campus"]}</p>
                    <p style="color: #777; margin: 5px 0; font-size: 0.9rem;"><strong>Faculdade:</strong> {plant_row["Faculdade"]}</p>
                    <p style="color: #777; margin: 5px 0; font-size: 0.9rem;"><strong>Potência:</strong> {plant_row["Potência (kWp)"]} kWp</p>
                    <p style="color: #777; margin: 5px 0; font-size: 0.9rem;"><strong>Geração:</strong> {plant_row["Geração Anual (kWh)"] / 1000:.0f} MWh/ano</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    def render_system_map(self):
        st.markdown("---")
        st.markdown("#### 📍 Localização das Usinas")

        df = self.manager.get_dataframe()
        df_with_coords = df[(df["Latitude"] != 0) & (df["Longitude"] != 0)]

        if len(df_with_coords) > 0:
            campus_colors = {
                "Darcy Ribeiro": "#2196F3",
                "Gama": "#4CAF50",
                "Ceilândia": "#FF9800",
                "Planaltina": "#9C27B0",
            }

            fig_map = go.Figure()

            for campus in df_with_coords["Campus"].unique():
                campus_data = df_with_coords[df_with_coords["Campus"] == campus]

                fig_map.add_trace(
                    go.Scattermapbox(
                        lat=campus_data["Latitude"],
                        lon=campus_data["Longitude"],
                        mode="markers",
                        marker=go.scattermapbox.Marker(
                            size=campus_data["Potência (kWp)"] / 10 + 10, color=campus_colors.get(campus, "#777777")
                        ),
                        text=[
                            f"{row['Nome']}<br>{row['Potência (kWp)']} kWp<br>{row['Campus']}"
                            for _, row in campus_data.iterrows()
                        ],
                        hoverinfo="text",
                        name=campus,
                    )
                )

            center_lat = df_with_coords["Latitude"].mean()
            center_lon = df_with_coords["Longitude"].mean()

            fig_map.update_layout(
                mapbox_style="open-street-map",
                mapbox=dict(center=go.layout.mapbox.Center(lat=center_lat, lon=center_lon), zoom=10),
                showlegend=True,
                height=500,
                margin={"r": 0, "t": 0, "l": 0, "b": 0},
            )

            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.info("📍 Dados de coordenadas não disponíveis para exibir o mapa")

    def render_charts_section(self):
        st.markdown("---")
        st.markdown("#### 📈 Análise do Sistema")

        col1, col2 = st.columns(2)

        with col1:
            fig1 = self.manager.create_power_by_campus_chart()
            if fig1:
                st.plotly_chart(fig1, use_container_width=True)

    def render_news_highlights(self):
        st.markdown("---")
        st.markdown("#### 📰 Destaques e Conquistas")
        overview = self.calculate_system_overview()

        news_data = [
            {
                "title": f"UnB possui {overview['total_plants']} usinas fotovoltaicas ativas",
                "summary": f"Sistema completo gera {overview['total_generation'] / 1000:.0f} MWh/ano com economia estimada de R$ {overview['estimated_annual_savings'] / 1000:.0f}k anuais.",
                "date": "2025",
                "highlight": True,
                "icon": "💰",
            },
            {
                "title": f"Evita emissão de {overview['co2_avoided']:.0f} toneladas de CO₂ por ano",
                "summary": f"O sistema fotovoltaico da UnB equivale ao plantio de {overview['trees_equivalent']:.0f} árvores em termos de impacto ambiental.",
                "date": "2025",
                "highlight": False,
                "icon": "🌱",
            },
            {
                "title": f"Sistema distribuído em {overview['campus_count']} campus",
                "summary": "Cobertura completa com usinas em todos os campus da UnB, promovendo sustentabilidade institucional.",
                "date": "2025",
                "highlight": False,
                "icon": "🏛️",
            },
            {
                "title": f"Mais de {overview['total_panels']:,} painéis solares instalados",
                "summary": "Infraestrutura robusta com tecnologia de ponta para máxima eficiência energética.",
                "date": "2025",
                "highlight": False,
                "icon": "🔆",
            },
        ]

        for i, news in enumerate(news_data):
            if news["highlight"]:
                st.markdown(
                    f"""
                    <div style="
                        background: linear-gradient(135deg, #E8F5E8 0%, #F1F8E9 100%);
                        border: 1px solid #4CAF50;
                        border-radius: 8px;
                        padding: 20px;
                        margin: 15px 0;
                        box-shadow: 0 2px 8px rgba(76, 175, 80, 0.2);
                    ">
                        <div style="display: flex; align-items: center; margin-bottom: 10px;">
                            <span style="font-size: 1.5rem; margin-right: 10px;">{news["icon"]}</span>
                            <h4 style="margin: 0; color: #2E7D32;">{news["title"]}</h4>
                        </div>
                        <p style="color: #1B5E20; margin: 10px 0; font-size: 1rem;">{news["summary"]}</p>
                        <small style="color: #4CAF50; font-weight: 500;">Atualizado: {news["date"]}</small>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                col1, col2 = st.columns([0.1, 0.9])
                with col1:
                    st.markdown(
                        f"<div style='font-size: 1.2rem; padding-top: 5px;'>{news['icon']}</div>",
                        unsafe_allow_html=True,
                    )
                with col2:
                    st.markdown(f"**{news['title']}**")
                    st.caption(f"{news['summary']} ({news['date']})")

    def render_environmental_impact(self):
        """Renderiza impacto ambiental"""
        st.markdown("---")
        st.markdown("#### 🌱 Impacto Ambiental")

        overview = self.calculate_system_overview()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(
                f"""
                <div style="
                    background: white;
                    border: 1px solid #E0E0E0;
                    border-left: 4px solid #4CAF50;
                    border-radius: 8px;
                    padding: 20px;
                    text-align: center;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                ">
                    <div style="color: #4CAF50; font-size: 2rem; margin-bottom: 10px;">🌍</div>
                    <div style="color: #2E7D32; font-size: 1.5rem; font-weight: 600;">{overview["co2_avoided"]:.0f}</div>
                    <div style="color: #777; font-size: 0.9rem;">Toneladas CO₂<br>evitadas/ano</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col2:
            st.markdown(
                f"""
                <div style="
                    background: white;
                    border: 1px solid #E0E0E0;
                    border-left: 4px solid #8BC34A;
                    border-radius: 8px;
                    padding: 20px;
                    text-align: center;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                ">
                    <div style="color: #8BC34A; font-size: 2rem; margin-bottom: 10px;">🌳</div>
                    <div style="color: #689F38; font-size: 1.5rem; font-weight: 600;">{overview["trees_equivalent"]:.0f}</div>
                    <div style="color: #777; font-size: 0.9rem;">Árvores<br>equivalentes</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col3:
            st.markdown(
                """
                <div style="
                    background: white;
                    border: 1px solid #E0E0E0;
                    border-left: 4px solid #2196F3;
                    border-radius: 8px;
                    padding: 20px;
                    text-align: center;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                ">
                    <div style="color: #2196F3; font-size: 2rem; margin-bottom: 10px;">⚡</div>
                    <div style="color: #1976D2; font-size: 1.5rem; font-weight: 600;">100%</div>
                    <div style="color: #777; font-size: 0.9rem;">Energia<br>renovável</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    def render_technical_specs(self):
        st.markdown("---")
        st.markdown("#### ⚙️ Especificações Técnicas")

        overview = self.calculate_system_overview()
        df = self.manager.get_dataframe()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**Sistema Geral**")
            st.caption(f"📊 Total de {overview['total_plants']} usinas")
            st.caption(f"⚡ {overview['total_capacity']:.0f} kWp instalados")
            st.caption(f"🏛️ {overview['campus_count']} campus atendidos")
            st.caption(f"🔧 {overview['plants_with_credentials']} configuradas")

        with col2:
            st.markdown("**Tecnologia**")
            panel_power_mode = df["Potência Painel (Wp)"].mode()
            panel_power = (
                panel_power_mode.iloc[0] if len(panel_power_mode) > 0 and panel_power_mode.iloc[0] > 0 else 275
            )

            st.caption(f"🔆 {overview['total_panels']:,} painéis solares")
            st.caption(f"⚡ {panel_power:.0f} Wp por painel típico")
            st.caption("🏭 Tecnologia Silício Monocristalino")
            st.caption("📡 Monitoramento em tempo real")

        with col3:
            st.markdown("**Performance**")
            avg_generation_per_kwp = (
                overview["total_generation"] / overview["total_capacity"] if overview["total_capacity"] > 0 else 1500
            )
            st.caption(f"📈 {avg_generation_per_kwp:.0f} kWh/kWp.ano")
            st.caption(f"💰 R$ {overview['estimated_annual_savings']:.0f} economia/ano")
            st.caption("🌞 Fator de capacidade: ~17%")
            st.caption("⚡ Eficiência média: 15-20%")

    def render_footer(self):
        st.markdown("---")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**Universidade de Brasília**")
            st.caption("Sistema Integrado de Energia Solar")
            st.caption("Todos os Campus - 4 unidades")
            st.caption("Monitoramento Centralizado")

        with col2:
            st.markdown("**Sustentabilidade**")
            st.caption("🌱 Energia 100% Renovável")
            st.caption("🌍 Redução de Emissões CO₂")
            st.caption("💰 Economia de Recursos Públicos")
            st.caption("📊 Transparência de Dados")

        with col3:
            st.markdown("**Tecnologia**")
            st.caption("☀️ Painéis Fotovoltaicos")
            st.caption("🔌 Inversores Inteligentes")
            st.caption("📡 Monitoramento IoT")
            st.caption("📊 Dashboard em Tempo Real")

        st.markdown("---")
        st.markdown(
            f"""
            <div style="text-align: center; color: #777; font-size: 0.85rem;">
                Sistema de Monitoramento Solar UnB | Atualizado em {datetime.now().strftime("%d/%m/%Y às %H:%M")} | 
                Dados carregados de: {self.manager.json_file_path.name}
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------------------------


def show_homepage():
    homepage = UnBSolarHomepage("data/solar_plants.json")

    st.set_page_config(
        page_title="Sistema Solar UnB",
        page_icon="🌞",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    if not homepage.manager.plants_data:
        st.error("❌ Erro ao carregar dados das usinas. Verifique o arquivo JSON.")
        st.info("💡 Certifique-se que o arquivo 'data/solar_plants.json' existe e está formatado corretamente.")

    homepage.render_hero_section()
    homepage.render_system_metrics()
    homepage.render_campus_overview()
    homepage.render_plants_overview()
    homepage.render_system_map()
    homepage.render_charts_section()
    homepage.render_news_highlights()
    homepage.render_environmental_impact()
    homepage.render_technical_specs()
    homepage.render_footer()

    with st.sidebar:
        st.header("⚙️ Configurações")
        if st.button("🔄 Recarregar Dados"):
            homepage.manager.reload_data()
            st.rerun()

        st.markdown("---")
        st.markdown("#### 📊 Status do Sistema")
        metrics = homepage.manager.get_summary_metrics()
        st.metric("Usinas Carregadas", metrics.get("total_plants", 0))
        st.metric("Última Atualização", datetime.now().strftime("%H:%M"))

        if homepage.manager.metadata:
            st.markdown("---")
            st.markdown("#### 📄 Informações do Arquivo")
            st.caption(f"**Fonte:** {homepage.manager.metadata.get('source', 'N/A')}")
            st.caption(f"**Versão:** {homepage.manager.metadata.get('version', 'N/A')}")
            last_updated = homepage.manager.metadata.get("last_updated", "N/A")
            if last_updated != "N/A":
                try:
                    dt = datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
                    last_updated = dt.strftime("%d/%m/%Y %H:%M")
                except:
                    pass
            st.caption(f"**Última Atualização:** {last_updated}")
