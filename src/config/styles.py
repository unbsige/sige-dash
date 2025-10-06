import plotly.io as pio
import streamlit as st


class ThemeManager:
    @staticmethod
    def get_main_css():
        return """
        <style>
            /* ===========================================
               CONFIGURAÇÕES GLOBAIS DA APLICAÇÃO
               =========================================== */
            .main > div {
                padding-top: 1rem;
            }
            
            .stApp {
                background-color: #f8fafc;
            }
            
            /* ===========================================
               ESTILOS MINIMALISTAS ORIGINAIS
               =========================================== */
            
            /* Selectbox minimalista */
            div[data-testid="stSelectbox"] > div > div {
                background-color: rgba(240, 242, 246, 0.5) !important;
                border: 1px solid rgba(49, 51, 63, 0.2) !important;
                border-radius: 4px !important;
                font-size: 0.85rem !important;
                min-height: 35px !important;
                height: 35px !important;
                transition: all 0.3s ease;
            }
            
            div[data-testid="stSelectbox"] > div > div:hover {
                border-color: rgba(52, 152, 219, 0.5) !important;
                box-shadow: 0 2px 8px rgba(52, 152, 219, 0.15) !important;
            }
            
            div[data-testid="stSelectbox"] label {
                font-size: 0.8rem !important;
                font-weight: 400 !important;
                color: #777 !important;
                margin-bottom: 2px !important;
            }
            
            /* Date Input minimalista */
            div[data-testid="stDateInput"] > div > div {
                background-color: rgba(240, 242, 246, 0.5) !important;
                border: 1px solid rgba(49, 51, 63, 0.2) !important;
                border-radius: 4px !important;
                font-size: 0.85rem !important;
                min-height: 35px !important;
                height: 35px !important;
                transition: all 0.3s ease;
            }
            
            div[data-testid="stDateInput"] > div > div:hover {
                border-color: rgba(52, 152, 219, 0.5) !important;
                box-shadow: 0 2px 8px rgba(52, 152, 219, 0.15) !important;
            }
            
            div[data-testid="stDateInput"] label {
                font-size: 0.8rem !important;
                font-weight: 400 !important;
                color: #777 !important;
                margin-bottom: 2px !important;
            }
            
            /* Input interno do date_input */
            div[data-testid="stDateInput"] input {
                background-color: transparent !important;
                border: none !important;
                font-size: 0.85rem !important;
                color: #333 !important;
                padding: 8px 12px !important;
            }
            
            /* Calendar icon minimalista */
            div[data-testid="stDateInput"] button {
                background-color: transparent !important;
                border: none !important;
                color: #777 !important;
                transition: color 0.3s ease;
                padding: 4px !important;
            }
            
            div[data-testid="stDateInput"] button:hover {
                color: #3498db !important;
            }
            
            /* Dropdown options minimalista */
            div[data-testid="stSelectbox"] ul {
                background-color: white !important;
                border: 1px solid rgba(49, 51, 63, 0.15) !important;
                border-radius: 4px !important;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
            }
            
            div[data-testid="stSelectbox"] li {
                font-size: 0.85rem !important;
                padding: 8px 12px !important;
                color: #333 !important;
            }
            
            div[data-testid="stSelectbox"] li:hover {
                background-color: rgba(52, 152, 219, 0.08) !important;
            }
            
            /* ===========================================
               COMPONENTES DE LAYOUT PRINCIPAL
               =========================================== */
            
            /* Header da aplicação */
            .header {
                background: white;
                padding: 1rem 2rem;
                border-radius: 8px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                margin-bottom: 1.5rem;
                border-left: 4px solid #3b82f6;
            }
            
            /* Container principal com gradiente */
            .main-container {
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                border-radius: 15px;
                padding: 20px;
                margin: 10px 0;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            }
            
            /* ===========================================
               FILTROS E CONTROLES MINIMALISTAS
               =========================================== */
            
            /* Container de filtros no topo */
            .top-filter-container {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(15px);
                border-radius: 20px;
                padding: 25px 30px;
                margin-bottom: 25px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.3);
            }
            
            /* Título das seções de filtro */
            .filter-title {
                font-size: 20px;
                font-weight: 700;
                color: #2c3e50;
                margin-bottom: 20px;
                text-align: center;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 10px;
            }
            
            /* Row de filtros lado a lado */
            .filter-row {
                display: flex;
                gap: 20px;
                align-items: end;
                justify-content: center;
                flex-wrap: wrap;
            }
            
            .filter-item {
                flex: 1;
                min-width: 200px;
                max-width: 300px;
            }
            
            .filter-label {
                font-weight: 600;
                color: #34495e;
                margin-bottom: 8px;
                font-size: 14px;
                display: flex;
                align-items: center;
                gap: 5px;
            }
            
            /* Toggle buttons minimalistas */
            .view-toggle {
                display: flex;
                background: #f1f5f9;
                border-radius: 6px;
                padding: 2px;
                margin: 1rem 0;
            }
            
            .toggle-btn {
                padding: 6px 12px;
                border: none;
                background: transparent;
                border-radius: 4px;
                cursor: pointer;
                transition: all 0.2s;
                font-size: 0.85rem;
                color: #777;
            }
            
            .toggle-btn.active {
                background: white;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                color: #333;
            }
            
            /* ===========================================
               CARDS E MÉTRICAS
               =========================================== */
            
            /* Cards de métricas modernos */
            .metric-card {
                background: rgba(255, 255, 255, 0.9);
                backdrop-filter: blur(10px);
                border-radius: 15px;
                padding: 20px;
                margin: 10px 0;
                border: 1px solid rgba(255, 255, 255, 0.2);
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
                transition: transform 0.3s ease;
            }
            
            .metric-card:hover {
                transform: translateY(-2px);
            }
            
            /* Cards de plantas minimalistas */
            .plant-card {
                background: white;
                border-radius: 6px;
                padding: 1.2rem;
                margin-bottom: 0.8rem;
                box-shadow: 0 1px 3px rgba(0,0,0,0.08);
                border-left: 3px solid;
                transition: all 0.2s ease;
            }
            
            .plant-card:hover {
                transform: translateY(-1px);
                box-shadow: 0 3px 8px rgba(0,0,0,0.12);
            }
            
            .plant-card.online { border-left-color: #10b981; }
            .plant-card.warning { border-left-color: #f59e0b; }
            .plant-card.error { border-left-color: #ef4444; }
            
            .plant-name {
                font-size: 1rem;
                font-weight: 600;
                color: #1f2937;
                margin-bottom: 0.4rem;
            }
            
            /* KPIs do topo minimalistas */
            .kpi-container {
                display: flex;
                gap: 0.8rem;
                margin-bottom: 1.5rem;
            }
            
            .kpi-card {
                flex: 1;
                background: white;
                padding: 1.2rem;
                border-radius: 6px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.08);
                text-align: center;
                border: 1px solid rgba(0,0,0,0.04);
            }
            
            .kpi-value {
                font-size: 1.8rem;
                font-weight: 700;
                color: #1f2937;
                margin: 0;
            }
            
            .kpi-label {
                font-size: 0.8rem;
                color: #6b7280;
                margin-top: 0.2rem;
                font-weight: 500;
            }
            
            .kpi-icon {
                font-size: 1.2rem;
                margin-bottom: 0.4rem;
                opacity: 0.7;
            }
            
            /* ===========================================
               HEADERS E TÍTULOS
               =========================================== */
            
            /* Header do período selecionado */
            .period-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 15px;
                margin-bottom: 20px;
                text-align: center;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
            }
            
            .period-header h3 {
                margin: 0;
                font-weight: 600;
                text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
            }
            
            /* ===========================================
               STATUS E INDICADORES MINIMALISTAS
               =========================================== */
            
            /* Status badges minimalistas */
            .status-badge {
                display: inline-block;
                padding: 2px 6px;
                border-radius: 10px;
                font-size: 0.7rem;
                font-weight: 500;
                margin-bottom: 0.8rem;
            }
            
            .status-online { background: #d1fae5; color: #065f46; }
            .status-warning { background: #fef3c7; color: #92400e; }
            .status-error { background: #fee2e2; color: #991b1b; }
            
            /* Indicadores de status circular */
            .status-indicator {
                display: inline-block;
                width: 8px;
                height: 8px;
                border-radius: 50%;
                margin-right: 6px;
            }
            
            .status-cached { background-color: #2ecc71; }
            .status-loading { background-color: #f39c12; }
            .status-error { background-color: #e74c3c; }
            
            /* ===========================================
               NAVEGAÇÃO E BOTÕES MINIMALISTAS
               =========================================== */
            
            /* Botões de navegação minimalistas */
            .nav-button {
                background: #f8fafc;
                border: 1px solid rgba(0,0,0,0.1);
                border-radius: 6px;
                width: 36px;
                height: 36px;
                color: #777;
                font-size: 14px;
                cursor: pointer;
                transition: all 0.2s ease;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .nav-button:hover {
                background: #e2e8f0;
                border-color: rgba(0,0,0,0.2);
                color: #333;
            }
            
            /* ===========================================
               MÉTRICAS E DADOS
               =========================================== */
            
            .metrics-row {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin: 0.8rem 0;
            }
            
            .metric-item {
                text-align: center;
            }
            
            .metric-value {
                font-size: 1.3rem;
                font-weight: 700;
                color: #1f2937;
                margin: 0;
            }
            
            .metric-label {
                font-size: 0.7rem;
                color: #6b7280;
                margin-top: 2px;
                font-weight: 500;
            }
            
            /* ===========================================
               PROGRESS BARS MINIMALISTAS
               =========================================== */
            
            .progress-container {
                margin: 0.8rem 0;
            }
            
            .progress-bar {
                width: 100%;
                height: 4px;
                background: #f3f4f6;
                border-radius: 2px;
                overflow: hidden;
            }
            
            .progress-fill {
                height: 100%;
                transition: width 0.3s ease;
            }
            
            .progress-good { background: #10b981; }
            .progress-warning { background: #f59e0b; }
            .progress-error { background: #ef4444; }
            
            /* ===========================================
               MINI CHARTS
               =========================================== */
            
            .mini-chart {
                height: 50px;
                margin: 0.8rem 0;
            }
            
            /* ===========================================
               INFO BOXES MINIMALISTAS
               =========================================== */
            
            .info-box {
                background: #f8fafc;
                color: #374151;
                padding: 12px 16px;
                border-radius: 6px;
                font-size: 0.85rem;
                margin-top: 12px;
                border-left: 3px solid #3b82f6;
            }
            
            .info-box strong {
                display: block;
                margin-bottom: 4px;
                font-weight: 600;
            }
            
            /* ===========================================
               TABELAS MINIMALISTAS
               =========================================== */
            
            .dataframe {
                border: none !important;
                font-size: 0.85rem !important;
            }
            
            .dataframe td, .dataframe th {
                border: none !important;
                padding: 8px 6px !important;
            }
            
            .dataframe th {
                background-color: #f8fafc !important;
                font-weight: 600 !important;
                color: #374151 !important;
                font-size: 0.8rem !important;
            }
            
            .dataframe tr:hover {
                background-color: #f9fafb !important;
            }
            
            /* ===========================================
               RESPONSIVIDADE
               =========================================== */
            
            @media (max-width: 768px) {
                .filter-row {
                    flex-direction: column;
                }
                
                .kpi-container {
                    flex-direction: column;
                }
                
                .metrics-row {
                    flex-direction: column;
                    gap: 0.8rem;
                }
                
                .top-filter-container {
                    padding: 12px 16px;
                }
                
                .metric-card {
                    padding: 12px;
                }
                
                div[data-testid="stSelectbox"] > div > div,
                div[data-testid="stDateInput"] > div > div {
                    min-height: 40px !important;
                    height: 40px !important;
                }
            }
        </style>
        """

    @staticmethod
    def configure_plotly():
        plotly_config = {
            "displayModeBar": False,
            "staticPlot": False,
            "responsive": True,
        }

        default_layout = dict(
            font=dict(family="Inter, Arial", size=12, color="#2c3e50"),
            plot_bgcolor="rgba(255,255,255,0.9)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=40, b=50, l=60, r=40),
            hoverlabel=dict(
                bgcolor="rgba(255,255,255,0.95)",
                bordercolor="rgba(0, 188, 212, 0.3)",
                font_size=11,
                font_color="#37474F",
                font_family="Inter",
            ),
            xaxis=dict(
                showgrid=True,
                gridcolor="rgba(0,0,0,0.08)",
                zeroline=False,
                showline=True,
                linecolor="rgba(0,0,0,0.2)",
                tickfont=dict(size=11, color="#37474F"),
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor="rgba(0,0,0,0.08)",
                zeroline=False,
                showline=False,
                tickfont=dict(size=11, color="#37474F"),
            ),
        )

        return plotly_config, default_layout

    @staticmethod
    def get_color_palette():
        return {
            "primary": "#00BCD4",  # Azul ciano
            "secondary": "#667eea",  # Azul roxo
            "success": "#10b981",  # Verde
            "warning": "#f59e0b",  # Amarelo
            "error": "#ef4444",  # Vermelho
            "info": "#74b9ff",  # Azul claro
            "dark": "#2c3e50",  # Azul escuro
            "light": "#f8fafc",  # Cinza claro
            "white": "#ffffff",  # Branco
            "transparent": "rgba(255,255,255,0.9)",
        }

    @staticmethod
    def get_status_colors():
        return {
            "online": {"primary": "#10b981", "background": "#d1fae5", "text": "#065f46"},
            "warning": {"primary": "#f59e0b", "background": "#fef3c7", "text": "#92400e"},
            "error": {"primary": "#ef4444", "background": "#fee2e2", "text": "#991b1b"},
        }

    @staticmethod
    def apply_theme():
        st.markdown(ThemeManager.get_main_css(), unsafe_allow_html=True)
        plotly_config, default_layout = ThemeManager.configure_plotly()

        if "plotly_config" not in st.session_state:
            st.session_state.plotly_config = plotly_config
            st.session_state.plotly_layout = default_layout
            st.session_state.color_palette = ThemeManager.get_color_palette()

    @staticmethod
    def get_chart_colors(chart_type="default"):
        colors = ThemeManager.get_color_palette()

        chart_colors = {
            "energy": {"bar": "rgba(0, 188, 212, 0.8)", "line": colors["primary"], "fill": "rgba(0, 188, 212, 0.15)"},
            "power": {"line": colors["primary"], "fill": "rgba(0, 188, 212, 0.15)"},
            "status": {"online": colors["success"], "warning": colors["warning"], "error": colors["error"]},
            "gradient": {
                "primary": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                "info": "linear-gradient(135deg, #74b9ff 0%, #0984e3 100%)",
                "success": "linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%)",
            },
        }

        return chart_colors.get(chart_type, chart_colors["energy"])


def render_col_divider(height=120, width=2, color="#566cc2", opacity=0.4, margin_top=2):
    st.markdown(
        f"""
        <div style="
            height: {height}px;
            width: {width}px;
            background-color: {color};
            margin: auto;
            margin-top: {margin_top}px;
            opacity: {opacity};
        "></div>
        """,
        unsafe_allow_html=True,
    )
