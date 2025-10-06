from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.data.solar_plants_manager import SolarDataManager


class UnBSolarHomepage:
    def __init__(self, json_file_path: str = "data/solar_plants.json"):
        self.manager = SolarDataManager(json_file_path)

    def render_hero_section(self):
        """Hero section minimalista e elegante"""
        st.markdown(
            """
            <div style="
                background: linear-gradient(135deg, #1565C0 0%, #2E7D32 100%);
                padding: 2rem 1.5rem;
                border-radius: 12px;
                margin-bottom: 2rem;
                color: white;
                text-align: center;
                box-shadow: 0 4px 20px rgba(21, 101, 192, 0.3);
            ">
                <h1 style="
                    font-size: 2.5rem; 
                    font-weight: 300; 
                    margin: 0 0 0.5rem 0;
                    letter-spacing: -0.02em;
                ">
                    Sistema Solar UnB
                </h1>
                <p style="
                    font-size: 1.1rem; 
                    margin: 0; 
                    opacity: 0.9;
                    font-weight: 300;
                ">
                    Monitoramento inteligente das usinas fotovoltaicas
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    def calculate_system_overview(self):
        """Calcula métricas do sistema usando dados corretos"""
        metrics = self.manager.get_summary_metrics()

        # Usar dados dos metadados quando disponível
        environmental = self.manager.environmental_impact
        total_capacity = metrics.get("total_power_kwp", 0)
        total_generation = metrics.get("total_generation_kwh", 0)

        # Cálculos baseados nos dados reais do JSON
        estimated_annual_savings = total_generation * 0.65  # R$0.65 por kWh
        co2_avoided = environmental.get("annual_co2_reduction_tons", 0)
        trees_equivalent = environmental.get("equivalent_trees_planted", 0)
        cars_off_road = environmental.get("equivalent_cars_off_road", 0)
        homes_powered = environmental.get("equivalent_homes_powered", 0)

        return {
            "total_capacity": total_capacity,
            "total_plants": metrics.get("total_plants", 0),
            "active_plants": len([p for p in self.manager.plants_data.values() if p.get("status") == "Ativa"]),
            "total_generation": total_generation,
            "estimated_annual_savings": estimated_annual_savings,
            "co2_avoided": co2_avoided,
            "trees_equivalent": trees_equivalent,
            "cars_off_road": cars_off_road,
            "homes_powered": homes_powered,
            "campus_count": metrics.get("campus_count", 0),
            "plants_with_credentials": len(self.manager.plants_data)
            - len(self.manager.get_plants_without_credentials()),
            "plants_with_device_id": len(self.manager.plants_data) - len(self.manager.get_plants_without_device_id()),
            "university": metrics.get("university", "Universidade de Brasília"),
            "last_updated": metrics.get("last_updated", ""),
        }

    def render_key_metrics(self):
        """Métricas principais em cards minimalistas"""
        overview = self.calculate_system_overview()

        # Cards principais
        col1, col2, col3, col4 = st.columns(4)

        metrics_data = [
            {"value": f"{overview['active_plants']}", "label": "Usinas Ativas", "icon": "🏭", "color": "#4CAF50"},
            {
                "value": f"{overview['total_capacity']:.0f}",
                "label": "kWp Instalados",
                "icon": "⚡",
                "color": "#2196F3",
            },
            {
                "value": f"{overview['total_generation'] / 1000:.1f}",
                "label": "MWh/ano",
                "icon": "🔋",
                "color": "#FF9800",
            },
            {
                "value": f"R$ {overview['estimated_annual_savings'] / 1000:.0f}k",
                "label": "Economia/ano",
                "icon": "💰",
                "color": "#9C27B0",
            },
        ]

        for i, (col, metric) in enumerate(zip([col1, col2, col3, col4], metrics_data)):
            with col:
                st.markdown(
                    f"""
                    <div style="
                        background: white;
                        border-radius: 12px;
                        padding: 1.5rem;
                        text-align: center;
                        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
                        border-left: 4px solid {metric["color"]};
                        transition: transform 0.2s ease;
                    ">
                        <div style="
                            font-size: 2rem; 
                            margin-bottom: 0.5rem;
                        ">{metric["icon"]}</div>
                        <div style="
                            color: {metric["color"]}; 
                            font-size: 1.8rem; 
                            font-weight: 600;
                            margin-bottom: 0.25rem;
                        ">{metric["value"]}</div>
                        <div style="
                            color: #777; 
                            font-size: 0.85rem;
                            font-weight: 500;
                        ">{metric["label"]}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    def render_campus_overview(self):
        """Visão geral elegante dos campus"""
        st.markdown("<br>", unsafe_allow_html=True)

        # Título com estilo
        st.markdown(
            """
            <h3 style="
                color: #1565C0; 
                font-weight: 400; 
                margin-bottom: 1.5rem;
                text-align: center;
            ">Campus da UnB</h3>
            """,
            unsafe_allow_html=True,
        )

        campus_analysis = self.manager.get_campus_analysis()

        if not campus_analysis:
            st.info("📍 Dados dos campus não disponíveis")
            return

        cols = st.columns(len(campus_analysis))

        campus_icons = {"Darcy Ribeiro": "🏛️", "Gama": "🔬", "Ceilândia": "🏥", "Planaltina": "🌾"}

        for i, (campus_name, campus_data) in enumerate(campus_analysis.items()):
            with cols[i]:
                icon = campus_icons.get(campus_name, "🏢")
                percentage = campus_data.get("percentage_of_total", 0)

                st.markdown(
                    f"""
                    <div style="
                        background: white;
                        border-radius: 12px;
                        padding: 1.5rem;
                        text-align: center;
                        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
                        margin-bottom: 1rem;
                        border-top: 3px solid #2196F3;
                    ">
                        <div style="font-size: 2.5rem; margin-bottom: 1rem;">{icon}</div>
                        <h4 style="
                            color: #1565C0; 
                            margin: 0 0 1rem 0;
                            font-weight: 500;
                        ">{campus_name}</h4>
                        <div style="color: #777; margin: 0.5rem 0; font-size: 0.9rem;">
                            <strong>{campus_data["plant_count"]}</strong> usinas
                        </div>
                        <div style="color: #777; margin: 0.5rem 0; font-size: 0.9rem;">
                            <strong>{campus_data["total_power"]:.0f}</strong> kWp
                        </div>
                        <div style="color: #777; margin: 0.5rem 0; font-size: 0.9rem;">
                            <strong>{percentage:.1f}%</strong> do total
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    def render_top_plants(self):
        """Principais usinas em layout elegante"""
        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown(
            """
            <h3 style="
                color: #1565C0; 
                font-weight: 400; 
                margin-bottom: 1.5rem;
                text-align: center;
            ">Principais Usinas</h3>
            """,
            unsafe_allow_html=True,
        )

        df = self.manager.get_dataframe()

        if df.empty:
            st.info("📊 Dados das usinas não disponíveis")
            return

        top_plants = df.nlargest(6, "Potência (kWp)")

        # Layout em grid 2x3
        for i in range(0, len(top_plants), 3):
            cols = st.columns(3)
            for j in range(3):
                if i + j < len(top_plants):
                    plant_row = top_plants.iloc[i + j]
                    with cols[j]:
                        self._render_plant_card_minimal(plant_row)

    def _render_plant_card_minimal(self, plant_row):
        """Card minimalista para plantas"""
        config_status = "🟢" if plant_row["Tem Device ID"] else "🟡"

        st.markdown(
            f"""
            <div style="
                background: white;
                border-radius: 12px;
                padding: 1.25rem;
                margin-bottom: 1rem;
                box-shadow: 0 2px 12px rgba(0,0,0,0.08);
                border-left: 4px solid #4CAF50;
                height: 160px;
            ">
                <div style="
                    display: flex; 
                    justify-content: space-between; 
                    align-items: flex-start; 
                    margin-bottom: 0.75rem;
                ">
                    <h5 style="
                        color: #1565C0; 
                        margin: 0; 
                        font-size: 1rem;
                        font-weight: 500;
                        line-height: 1.2;
                    ">{plant_row["Nome"]}</h5>
                    <span style="font-size: 1rem;" title="Configuração">{config_status}</span>
                </div>
                
                <div style="color: #777; font-size: 0.85rem; line-height: 1.4;">
                    <div style="margin-bottom: 0.25rem;">
                        <strong>Campus:</strong> {plant_row["Campus"]}
                    </div>
                    <div style="margin-bottom: 0.25rem;">
                        <strong>Potência:</strong> {plant_row["Potência (kWp)"]} kWp
                    </div>
                    <div style="margin-bottom: 0.25rem;">
                        <strong>Geração:</strong> {plant_row["Geração Anual (kWh)"] / 1000:.1f} MWh/ano
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    def render_environmental_impact(self):
        """Impacto ambiental com dados corretos do JSON"""
        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown(
            """
            <h3 style="
                color: #1565C0; 
                font-weight: 400; 
                margin-bottom: 1.5rem;
                text-align: center;
            ">Impacto Ambiental</h3>
            """,
            unsafe_allow_html=True,
        )

        overview = self.calculate_system_overview()

        col1, col2, col3, col4 = st.columns(4)

        env_metrics = [
            {"icon": "🌍", "value": f"{overview['co2_avoided']:.0f}", "unit": "ton CO₂/ano", "color": "#4CAF50"},
            {
                "icon": "🌳",
                "value": f"{overview['trees_equivalent']:,.0f}",
                "unit": "árvores equiv.",
                "color": "#8BC34A",
            },
            {"icon": "🚗", "value": f"{overview['cars_off_road']:.0f}", "unit": "carros equiv.", "color": "#FF5722"},
            {"icon": "🏠", "value": f"{overview['homes_powered']:,.0f}", "unit": "residências", "color": "#2196F3"},
        ]

        for col, metric in zip([col1, col2, col3, col4], env_metrics):
            with col:
                st.markdown(
                    f"""
                    <div style="
                        background: white;
                        border-radius: 12px;
                        padding: 1.5rem;
                        text-align: center;
                        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
                        border-top: 3px solid {metric["color"]};
                    ">
                        <div style="
                            color: {metric["color"]}; 
                            font-size: 2rem; 
                            margin-bottom: 0.75rem;
                        ">{metric["icon"]}</div>
                        <div style="
                            color: {metric["color"]}; 
                            font-size: 1.5rem; 
                            font-weight: 600;
                            margin-bottom: 0.25rem;
                        ">{metric["value"]}</div>
                        <div style="
                            color: #777; 
                            font-size: 0.8rem;
                            font-weight: 500;
                            line-height: 1.2;
                        ">{metric["unit"]}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    def render_system_map(self):
        """Mapa elegante das usinas"""
        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown(
            """
            <h3 style="
                color: #1565C0; 
                font-weight: 400; 
                margin-bottom: 1.5rem;
                text-align: center;
            ">Localização das Usinas</h3>
            """,
            unsafe_allow_html=True,
        )

        df = self.manager.get_dataframe()

        if df.empty:
            st.info("📍 Dados de localização não disponíveis")
            return

        df_with_coords = df[(df["Latitude"] != 0) & (df["Longitude"] != 0)]

        if len(df_with_coords) == 0:
            st.info("📍 Coordenadas não disponíveis para exibir o mapa")
            return

        # Cores elegantes para campus
        campus_colors = {
            "Darcy Ribeiro": "#1565C0",
            "Gama": "#2E7D32",
            "Ceilândia": "#FF6F00",
            "Planaltina": "#7B1FA2",
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
                        size=[max(10, p / 15 + 8) for p in campus_data["Potência (kWp)"]],
                        color=campus_colors.get(campus, "#777777"),
                        opacity=0.8,
                    ),
                    text=[
                        f"<b>{row['Nome']}</b><br>"
                        + f"Potência: {row['Potência (kWp)']} kWp<br>"
                        + f"Campus: {row['Campus']}<br>"
                        + f"Geração: {row['Geração Anual (kWh)'] / 1000:.1f} MWh/ano"
                        for _, row in campus_data.iterrows()
                    ],
                    hoverinfo="text",
                    name=campus,
                    showlegend=True,
                )
            )

        center_lat = df_with_coords["Latitude"].mean()
        center_lon = df_with_coords["Longitude"].mean()

        fig_map.update_layout(
            mapbox_style="open-street-map",
            mapbox=dict(center=go.layout.mapbox.Center(lat=center_lat, lon=center_lon), zoom=11),
            showlegend=True,
            height=500,
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )

        st.plotly_chart(fig_map, use_container_width=True)

    def render_power_chart(self):
        """Gráfico de potência por campus"""
        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown(
            """
            <h3 style="
                color: #1565C0; 
                font-weight: 400; 
                margin-bottom: 1.5rem;
                text-align: center;
            ">Distribuição por Campus</h3>
            """,
            unsafe_allow_html=True,
        )

        fig = self.manager.create_power_by_campus_chart()
        if fig:
            # Personalizar estilo do gráfico
            fig.update_layout(
                font_family="Arial",
                title_font_size=16,
                showlegend=False,
                height=400,
                margin=dict(t=50, l=50, r=50, b=50),
            )
            fig.update_traces(marker_line_width=0, textfont_size=12)
            st.plotly_chart(fig, use_container_width=True)

    def render_footer(self):
        """Footer minimalista"""
        st.markdown("<br><br>", unsafe_allow_html=True)

        overview = self.calculate_system_overview()
        last_updated = overview.get("last_updated", "")

        if last_updated:
            try:
                dt = datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
                last_updated_formatted = dt.strftime("%d/%m/%Y às %H:%M")
            except:
                last_updated_formatted = "N/A"
        else:
            last_updated_formatted = datetime.now().strftime("%d/%m/%Y às %H:%M")

        st.markdown(
            f"""
            <div style="
                text-align: center; 
                color: #999; 
                font-size: 0.85rem;
                padding: 2rem 0 1rem 0;
                border-top: 1px solid #eee;
                margin-top: 2rem;
            ">
                <div style="margin-bottom: 0.5rem;">
                    <strong>{overview["university"]}</strong>
                </div>
                <div>
                    Sistema atualizado em {last_updated_formatted} • 
                    {overview["total_plants"]} usinas monitoradas
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def show_homepage():
    """Função principal para exibir a homepage"""
    st.set_page_config(
        page_title="Sistema Solar UnB",
        page_icon="🌞",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    # CSS customizado para estilo minimalista
    st.markdown(
        """
        <style>
        .main > div {
            padding-top: 2rem;
        }
        .stApp > header {
            background-color: transparent;
        }
        .stApp {
            background-color: #fafafa;
        }
        /* Ocultar menu do Streamlit */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        </style>
        """,
        unsafe_allow_html=True,
    )

    homepage = UnBSolarHomepage("data/solar_plants.json")

    # Verificar se dados foram carregados
    if not homepage.manager.plants_data:
        st.error("❌ Erro ao carregar dados das usinas.")
        st.info("💡 Verifique se o arquivo 'data/solar_plants.json' existe e está formatado corretamente.")

        # Mostrar detalhes do erro se disponível
        issues = homepage.manager.validate_data_integrity()
        if issues:
            st.error("**Problemas encontrados:**")
            for issue in issues[:5]:  # Mostrar apenas os primeiros 5
                st.error(f"• {issue}")
        return

    # Renderizar seções
    homepage.render_hero_section()
    homepage.render_key_metrics()
    homepage.render_campus_overview()
    homepage.render_top_plants()
    homepage.render_environmental_impact()
    homepage.render_system_map()
    homepage.render_power_chart()
    homepage.render_footer()

    # Sidebar minimalista
    with st.sidebar:
        st.markdown("### ⚙️ Sistema")

        if st.button("🔄 Atualizar", use_container_width=True):
            homepage.manager.reload_data()
            st.rerun()

        st.markdown("---")

        metrics = homepage.manager.get_summary_metrics()
        st.markdown("**Status**")
        st.caption(f"✅ {metrics.get('total_plants', 0)} usinas carregadas")
        st.caption(
            f"🔧 {len(homepage.manager.plants_data) - len(homepage.manager.get_plants_without_device_id())} configuradas"
        )
        st.caption(f"⚡ {metrics.get('total_power_kwp', 0):.0f} kWp total")

        if homepage.manager.metadata:
            st.markdown("---")
            st.markdown("**Dados**")
            last_updated = homepage.manager.metadata.get("last_updated", "N/A")
            if last_updated != "N/A":
                try:
                    dt = datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
                    last_updated = dt.strftime("%d/%m %H:%M")
                except:
                    pass
            st.caption(f"📅 Atualizado: {last_updated}")
            st.caption(f"🏛️ {homepage.manager.metadata.get('campus_count', 0)} campus")
