import plotly.io as pio
import streamlit as st


class ThemeManager:
    """Gerenciador centralizado de temas e estilos da aplicação."""

    @staticmethod
    def get_main_css():
        """Retorna o CSS principal da aplicação."""
        return """
        <style>
        /* ============================================
           LAYOUT PRINCIPAL E TIPOGRAFIA
           ============================================ */
        .main > div {
            padding-top: 1rem;
        }
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 1rem;
        }
        h1 {
            font-size: 2rem;
            margin-bottom: 0.5rem;
            color: #1f1f1f;
        }

        /* ============================================
           CARDS DE SELEÇÃO DE PLANTAS
           ============================================ */
        .plant-card {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 1rem;
            text-align: center;
            transition: all 0.2s;
        }
        .plant-card:hover {
            border-color: #0066cc;
            background: #f0f8ff;
        }

        /* ============================================
           DIVISORES E DESTAQUES DE SEÇÃO
           ============================================ */
        .section-divider {
            margin: 2rem 0 1rem 0;
            border-top: 1px solid #e9ecef;
            padding-top: 1.5rem;
        }
        .nbr-highlight {
            background-color: #f0f2f6;
            padding: 15px;
            border-radius: 10px;
            border-left: 5px solid #1f77b4;
            margin: 10px 0;
        }

        /* ============================================
           GRUPOS DE PARÂMETROS
           ============================================ */
        .parameter-group {
            background-color: var(--background-color-secondary, #f8f9fa);
            color: var(--text-color, #262730);
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
            border-left: 4px solid #007acc;
        }

        /* ============================================
           CABEÇALHOS DE ETAPAS
           ============================================ */
        .step-header {
            background-color: var(--background-color-secondary, #e3f2fd);
            color: var(--text-color, #1565c0);
            padding: 10px 15px;
            border-radius: 5px;
            border-left: 4px solid #2196f3;
            margin-bottom: 15px;
        }

        /* ============================================
           ELEMENTOS DE FORMULÁRIO
           ============================================ */
        .stSlider > label {
            font-size: 0.8rem;
            font-weight: 500;
            color: var(--text-color, #2c3e50);
            margin-bottom: 0.3rem;
        }

        /* ============================================
           GRÁFICOS PLOTLY - INTEGRAÇÃO COM TEMA
           ============================================ */
        .js-plotly-plot .plotly .main-svg {
            background: transparent !important;
        }
        .js-plotly-plot .plotly .bg {
            fill: transparent !important;
        }
        
        /* ============================================
           SUPORTE A MODO ESCURO
           ============================================ */
        @media (prefers-color-scheme: dark) {
            h1 {
                color: #fafafa;
            }
            .parameter-group {
                background-color: #2b2b35;
                color: #fafafa;
            }
            .step-header {
                background-color: #1e3a5f;
                color: #90caf9;
            }
            .stSlider > label {
                color: #fafafa;
            }
            .plant-card {
                background: #2b2b35;
                border-color: #3f4045;
                color: #fafafa;
            }
            .plant-card:hover {
                border-color: #0066cc;
                background: #1e3a5f;
            }
            .nbr-highlight {
                background-color: #2b2b35;
                border-left-color: #90caf9;
            }
        }

        /* ============================================
           DETECÇÃO ESPECÍFICA DO TEMA STREAMLIT
           ============================================ */
        .stApp[data-theme="dark"] h1,
        .stApp[theme-base="dark"] h1 {
            color: #fafafa;
        }
        
        .stApp[data-theme="dark"] .parameter-group,
        .stApp[theme-base="dark"] .parameter-group {
            background-color: #2b2b35;
            color: #fafafa;
        }
        
        .stApp[data-theme="dark"] .step-header,
        .stApp[theme-base="dark"] .step-header {
            background-color: #1e3a5f;
            color: #90caf9;
        }
        
        .stApp[data-theme="dark"] .plant-card,
        .stApp[theme-base="dark"] .plant-card {
            background: #2b2b35;
            border-color: #3f4045;
            color: #fafafa;
        }
        
        .stApp[data-theme="dark"] .nbr-highlight,
        .stApp[theme-base="dark"] .nbr-highlight {
            background-color: #2b2b35;
            border-left-color: #90caf9;
        }
        </style>
        """

    @staticmethod
    def configure_plotly():
        """Configura o Plotly para integração com Streamlit."""
        # Template básico que funciona com ambos os temas
        pio.templates.default = "plotly_white"

        # Configurações globais para transparência
        pio.templates["plotly_white"].layout.update(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")

    @staticmethod
    def apply_theme():
        """Aplica todos os estilos da aplicação."""
        # Aplicar CSS principal
        st.markdown(ThemeManager.get_main_css(), unsafe_allow_html=True)

        # Configurar Plotly
        ThemeManager.configure_plotly()

    @staticmethod
    def get_theme_colors():
        """Retorna cores adaptativas para gráficos."""
        try:
            current_theme = st.get_option("theme.base")
            if current_theme == "dark":
                return {
                    "primary": "#FF6B35",
                    "secondary": "#1E88E5",
                    "success": "#4CAF50",
                    "warning": "#FF9800",
                    "error": "#F44336",
                    "text": "#FAFAFA",
                    "grid": "rgba(255,255,255,0.1)",
                }
            else:
                return {
                    "primary": "#FF6B35",
                    "secondary": "#1E88E5",
                    "success": "#4CAF50",
                    "warning": "#FF9800",
                    "error": "#F44336",
                    "text": "#262730",
                    "grid": "rgba(0,0,0,0.1)",
                }
        except:
            # Fallback para cores neutras
            return {
                "primary": "#FF6B35",
                "secondary": "#1E88E5",
                "success": "#4CAF50",
                "warning": "#FF9800",
                "error": "#F44336",
                "text": "currentColor",
                "grid": "rgba(128,128,128,0.2)",
            }
