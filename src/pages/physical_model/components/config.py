from typing import Any, Dict

import numpy as np
import streamlit as st


def configure_pv_model_params(default_params: dict[str, Any]) -> dict[str, Any]:
    """
    Configura parâmetros específicos do modelo PV com interface especializada.

    Args:
        default_params: Parâmetros padrão do modelo

    Returns:
        Dict com parâmetros configurados pelo usuário
    """
    st.subheader("⚙️ Configuração do Modelo Físico PV")

    configured_params = {}

    # Seção 1: Parâmetros do Sistema
    with st.expander("🏭 Parâmetros do Sistema Fotovoltaico", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            configured_params["capacity_kwp"] = st.number_input(
                "Capacidade (kWp)",
                min_value=1.0,
                max_value=1000.0,
                value=default_params["capacity_kwp"],
                step=1.0,
                help="Capacidade nominal do sistema fotovoltaico",
            )

            configured_params["noct"] = st.slider(
                "NOCT (°C)",
                min_value=35.0,
                max_value=50.0,
                value=default_params["noct"],
                step=0.5,
                help="Temperatura Nominal de Operação da Célula",
            )

        with col2:
            configured_params["temp_coeff"] = st.slider(
                "Coeficiente de Temperatura (%/°C)",
                min_value=-0.006,
                max_value=-0.002,
                value=default_params["temp_coeff"],
                step=0.0001,
                format="%.4f",
                help="Coeficiente de temperatura da potência",
            )

            configured_params["irrad_coeff"] = st.slider(
                "Coeficiente de Irradiância",
                min_value=0.01,
                max_value=0.05,
                value=default_params["irrad_coeff"],
                step=0.001,
                format="%.3f",
                help="Coeficiente de correção por irradiância",
            )

    # Seção 2: Coeficientes de Perda DC
    with st.expander("⚡ Coeficientes de Perda DC", expanded=True):
        st.markdown("**Equação:** `cpdc = G / (G + a0 + a1*G + a2*G²)`")

        col1, col2, col3 = st.columns(3)

        with col1:
            configured_params["a0"] = st.slider(
                "a0 (Perdas Fixas)",
                min_value=0.005,
                max_value=0.08,
                value=default_params["a0"],
                step=0.001,
                format="%.3f",
                help="Perdas independentes da irradiância",
            )

        with col2:
            configured_params["a1"] = st.slider(
                "a1 (Termo Linear)",
                min_value=-0.25,
                max_value=0.02,
                value=default_params["a1"],
                step=0.01,
                format="%.3f",
                help="Correção linear com irradiância",
            )

        with col3:
            configured_params["a2"] = st.slider(
                "a2 (Termo Quadrático)",
                min_value=0.15,
                max_value=0.45,
                value=default_params["a2"],
                step=0.01,
                format="%.3f",
                help="Perdas em alta irradiância",
            )

        # Visualização da curva de perdas DC
        if st.checkbox("📊 Visualizar Curva de Perdas DC"):
            # show_dc_loss_curve(configured_params["a0"], configured_params["a1"], configured_params["a2"])
            pass

    # Seção 3: Coeficientes do Inversor
    with st.expander("🔄 Coeficientes do Inversor", expanded=False):
        st.markdown("**Equação NBR 16274:** `Pac = [-(k1+1) + √((k1+1)² - 4k2(k0-Pdc/Pni))] / (2k2)`")

        col1, col2, col3 = st.columns(3)

        with col1:
            configured_params["k0"] = st.slider(
                "k0 (Termo Constante)",
                min_value=-0.03,
                max_value=-0.008,
                value=default_params["k0"],
                step=0.001,
                format="%.4f",
            )

        with col2:
            configured_params["k1"] = st.slider(
                "k1 (Termo Linear)",
                min_value=0.008,
                max_value=0.025,
                value=default_params["k1"],
                step=0.001,
                format="%.4f",
            )

        with col3:
            configured_params["k2"] = st.slider(
                "k2 (Termo Quadrático)",
                min_value=-0.008,
                max_value=-0.002,
                value=default_params["k2"],
                step=0.0001,
                format="%.4f",
            )

    # Seção 4: Configurações do Modelo
    with st.expander("⚙️ Configurações Avançadas", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            configured_params["apply_ac_loss"] = st.checkbox(
                "Aplicar Perdas AC",
                value=default_params["apply_ac_loss"],
                help="Inclui perdas em cabeamento AC, transformador, etc.",
            )

            configured_params["apply_dc_loss"] = st.checkbox(
                "Aplicar Perdas DC",
                value=default_params["apply_dc_loss"],
                help="Aplica modelo de perdas DC com coeficientes a0, a1, a2",
            )

        with col2:
            configured_params["use_nbr_eff"] = st.checkbox(
                "Usar Eficiência NBR",
                value=default_params["use_nbr_eff"],
                help="Usa fórmula NBR 16274 ao invés de curva empírica",
            )

            configured_params["optimize_coefficients"] = st.checkbox(
                "Otimizar Coeficientes",
                value=default_params["optimize_coefficients"],
                help="Otimiza coeficientes a0, a1, a2 durante treinamento",
            )

        if configured_params["optimize_coefficients"]:
            configured_params["optimization_method"] = st.selectbox(
                "Método de Otimização",
                options=["L-BFGS-B", "TNC", "SLSQP", "Powell"],
                index=["L-BFGS-B", "TNC", "SLSQP", "Powell"].index(default_params["optimization_method"]),
                help="Algoritmo de otimização para coeficientes",
            )

    return configured_params
