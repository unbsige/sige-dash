import streamlit as st
import plotly.graph_objects as go
from feature_utils import create_features
from load_data import load_data
from pages.model_ml.components.features import select_features
from pages.model_ml.components.plants import select_plant
from pages.model_ml.components.split_dataset import split_train_test

from pages.model_ml.components.train_model import train_evaluate_model

st.set_page_config(
    page_title="Machine Learning",
    page_icon=":chart_with_upwards_trend:",
    layout="wide",
)

if st.sidebar.button("🔄 Novo Experimento (Reset Geral)"):
    st.session_state.clear()
    st.rerun()

if "df_prod" not in st.session_state:
    load_data()

st.title("Machine Learning")
st.subheader("Conjuntos de dados")

df_prod = st.session_state.df_prod
df_rad_solcast = st.session_state.df_rad_solcast
df_rad_tempook = st.session_state.df_rad_tempook

with st.expander("⚡ :green[Dados de Produção de energia]"):
    st.dataframe(df_prod, use_container_width=True)

with st.expander("☀️ :green[Dados Irradiação solar - Solcast]"):
    st.dataframe(df_rad_solcast, use_container_width=True)

with st.expander("☀️ :green[Dados Irradiação solar - TempoOK]"):
    st.dataframe(df_rad_tempook, use_container_width=True)

# ==================================================================================================================
st.write(" ")
st.divider()
st.subheader("1. Seleção do inversor ou medidor")
target = select_plant()


df_features_all = create_features(df_prod[[target]], target)
# ==================================================================================================================

st.write(" ")
st.divider()
st.subheader("2. Seleção de recursos")
df_features = select_features(df_features_all, target, df_rad_tempook, df_rad_solcast)

if df_features is None:
    st.stop()
# ==================================================================================================================

st.divider()
st.sidebar.divider()
st.subheader("3. Dividir conjunto de dados em treino e teste")

datasets = split_train_test(df_features, target)
# ==================================================================================================================

st.divider()
st.sidebar.divider()
st.subheader("4. Seleção do Modelo de Machine Learning")

model = st.radio(
    "Selecione o modelo de Machine Learning",
    ("XGBoost", "Physical", "LightGBM"),
)

if st.button(f"🧪  Iniciar Experimento: {model}"):
    df_pred, metrics = train_evaluate_model(model, datasets, target)
else:
    st.warning("Clique em iniciar experimento.")
    st.stop()
# ==================================================================================================================

st.divider()
st.write("")
st.write(f"### Resultados: Previsão de Produção de Energia - {model}")


# ==================================================================================================================

cols = st.columns(4)
for col, (key, value) in zip(cols, metrics.items()):
    col.metric(
        label=f"{key.upper()}",
        label_visibility="collapsed",
        value=round(value, 4),
        delta=f"{key.upper()}",
        delta_color="normal"
    )

graph = [
    go.Scatter(
        x=df_pred.index,
        y=df_pred["y_true"],
        mode='lines',
        line=dict(color="darkcyan"),
        name='test set'
    ),

    go.Scatter(
        x=df_pred.index,
        y=df_pred["y_pred"],
        mode='lines',
        line=dict(color="coral"),
        name='predict'
    )
]
layout = dict(
    height=600,
    title={
        "text": f"Produção de Energia: previsão com modelo {model}", 
        "y": 0.9,
        "x": 0.5,
        "xanchor": "center",
        "yanchor": "top",
        "font": {"size": 20}
    },
    yaxis=dict(title="Produção de Energia (kWh)"),
    xaxis=dict(
        title="",
        type='date',
        rangeslider=dict(visible=True),
        rangeselector=dict(
            buttons=[
                dict(count=1, label='1d', step='day', stepmode='backward'),
                dict(count=3, label='3d', step='day', stepmode='backward'),
                dict(count=7, label='1s', step='day', stepmode='backward'),
                dict(step='all'),
            ],
            font=dict(size=13),
            bordercolor="#0072B2",
            borderwidth=1,
            activecolor="#0072B2",
        ),
    ),
)
fig = go.Figure(data=graph, layout=layout)
st.plotly_chart(fig, use_container_width=True)
