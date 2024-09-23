import pandas as pd
import streamlit as st
from config.settings import (
    CYCLIC_FEATURES,
    IRRADIATION_FEATURES,
    LAG_FEATURES,
    RADIAL_FEATURES,
    SINCE_FEATURES,
    TIME_FEATURES,
    WINDOWS_FEATURES,
)


def multiselect_with_all(title, options, key=None):
    all_selected = st.checkbox(f"Selecionar Todos {title}", key=f"all_{key or title}")
    return st.multiselect(title, options, default=options if all_selected else None, key=key or title)


def select_feature_group(title, options, col):
    with col:
        selected = multiselect_with_all(title, ["todos"] + options)
        return options if "todos" in selected else [f for f in selected if f != "todos"]


def display_data_summary(df_selected, target, features):
    with st.expander("2. Visualização dos Dados", expanded=True):
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown("##### Resumo das Características Selecionadas")
            st.metric("Total de Features", len(features))
            st.metric("Target", target)
        with col2:
            st.markdown("##### *Features (X)* - Variáveis Independentes")
            st.dataframe(df_selected[features].head(4), hide_index=True)


def select_features(df_features_all, target, df_rad_tempook, df_rad_solcast):
    if 'features' not in st.session_state:
        st.session_state.features = []
    if 'df_selected' not in st.session_state:
        st.session_state.df_selected = None

    df = df_features_all.copy()

    with st.expander("1. Seleção de Recursos", expanded=True):
        st.markdown("### A) Recursos Internos")

        feature_sets = [
            ("Recursos de Tempo", TIME_FEATURES),
            ("Recursos Cíclicos", CYCLIC_FEATURES),
            ("Recursos de Tempo Desde", SINCE_FEATURES),
            ("Recursos Radiais", RADIAL_FEATURES),
            ("Recursos de Lag", LAG_FEATURES),
            ("Recursos de Janela", WINDOWS_FEATURES),
        ]

        cols = st.columns(3)
        features = []
        for idx, (title, options) in enumerate(feature_sets):
            features.extend(select_feature_group(title, options, cols[idx % len(cols)]))

        st.markdown("### B) Recursos Externos")

        cols = st.columns(3)
        with cols[0]:
            use_irradiation_data = st.toggle("Utilizar Dados de Irradiação Solar", False)
            if use_irradiation_data:
                source = st.selectbox("Selecione a Fonte de Dados", ["Solcast", "TempoOK"])
                df_radiation = df_rad_solcast if source == "Solcast" else df_rad_tempook
                df = pd.concat([df, df_radiation], axis=1)

                irradiation_features = select_feature_group("Recursos de Irradiação", IRRADIATION_FEATURES, cols[1])
                features.extend(irradiation_features)

    if not features:
        st.warning("⚠️ Nenhum recurso selecionado. Selecione pelo menos um recurso para continuar.")
        return None

    df_selected = df[[target] + features]
    display_data_summary(df_selected, target, features)

    col1, col2, col3 = st.columns([2, 2, 6])
    with col1:
        if st.button("🔄 Resetar Seleções"):
            st.session_state.features = []
            st.session_state.df_selected = None
            st.rerun()

    with col2:
        confirm_clicked = st.button("✅ Confirmar Seleção", key="confirm_button")

    with col3:
        if confirm_clicked:
            st.session_state.features = features
            st.session_state.df_selected = df_selected
            st.success(f"✅ Seleção confirmada! Recursos selecionados: {', '.join(features)}")

    return st.session_state.df_selected
