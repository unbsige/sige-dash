import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import xgboost as xgb

from config.settings import (
    END_DATE,
    IRRAD_FEATURES,
    SPLIT_DATE,
    START_DATE,
    TARGET_COLS,
    TIME_FEATURES,
)
from metric_utils import calculate_metrics

st.set_page_config(
    page_title="Machine Learning",
    page_icon=":chart_with_upwards_trend:",
    layout="wide",
)

if "df_prod" not in st.session_state:
    st.stop()

st.title("Visualização dos Dados")
st.subheader("Dataframe Producao de energia")
df_prod = st.session_state.df_prod
df_rad = st.session_state.df_rad
df_prod = df_prod.drop(columns=["month_name", "day_name"])

st.dataframe(df_prod.head(), use_container_width=True)

st.subheader("Dataframe Irradiância Solar")
st.dataframe(df_rad.head(), use_container_width=True)
use_irad = st.checkbox("Utilizar dataframe de irradiância como recurso para previsão de produção de energia")

st.sidebar.subheader("1. Preparar dataframe")
target = st.sidebar.selectbox("Selecione coluna target", options=TARGET_COLS)
time_features = st.sidebar.multiselect("Selecione recursos de tempo", options=TIME_FEATURES)

if use_irad:
    df = pd.concat([df_prod, df_rad], axis=1)
    irrad_features = st.sidebar.multiselect("Selecione recursos de irradiacao", options=IRRAD_FEATURES)
    features = time_features + irrad_features
else:
    df = df_prod.copy()
    features = time_features

st.subheader("1. Preparar dataframe para projeto de ML")
if not target or not features:
    st.warning("Selecione a coluna de target e no minimo uma coluna de recurso")
    st.stop()

df_ml = df[features + [target]].copy()
df_base = df_ml.loc[START_DATE:END_DATE].copy()
df_eval = df_ml.loc[END_DATE:].copy()

# colorir a coluna target no dataframe
st.dataframe(df_base.head(), column_config={"target": {"color": "coral"}})

st.divider()
st.subheader("2. Dividir dataframe em treino e teste")

st.sidebar.divider()
st.sidebar.subheader("2. Selecione a data de corte do dataset de teste")
split_date = st.sidebar.date_input("Data de corte", value=SPLIT_DATE)

df_train = df_base.loc[:split_date]
df_test = df_base.loc[split_date:]

c1, c2 = st.columns(2)
with c1.expander("Dataset de treino - df_train"):
    start_date = df_train.index.min().strftime('%d-%m-%Y %H:%M:%S')
    end_date = df_train.index.max().strftime('%d-%m-%Y %H:%M:%S')
    n_rows = df_train.shape[0]

    c11, c12 = st.columns(2)
    c11.metric(
        label="Data de inicio",
        label_visibility="collapsed",
        value=start_date,
        delta="Inicio do dataset de treino",
        delta_color="normal",
    )
    c12.metric(
        label="Data de fim",
        label_visibility="collapsed",
        value=end_date,
        delta="Final do dataset de treino",
        delta_color="normal",
    )
    st.dataframe(df_train, use_container_width=True)
    st.write(f"Numero de linhas: {n_rows}")

with c2.expander("Dataset de treino - df_test"):
    start_date = df_test.index.min().strftime('%d-%m-%Y %H:%M:%S')
    end_date = df_test.index.max().strftime('%d-%m-%Y %H:%M:%S')
    n_rows = df_test.shape[0]

    c11, c12 = st.columns(2)
    c11.metric(
        label="Data de inicio",
        label_visibility="collapsed",
        value=start_date,
        delta="Inicio do dataset de teste",
        delta_color="normal",
    )
    c12.metric(
        label="Data de fim",
        label_visibility="collapsed",
        value=end_date,
        delta="Final do dataset de teste",
        delta_color="normal",
    )
    st.dataframe(df_test, use_container_width=True)
    st.write(f"Numero de linhas: {n_rows}")


graph = [
    go.Scatter(
        x=df_train.index,
        y=df_train[target],
        mode='lines',
        line=dict(color="darkcyan"),
        name='train set'
    ),

    go.Scatter(
        x=df_test.index,
        y=df_test[target],
        mode='lines',
        line=dict(color="coral"),
        name='test set'
    )
]
layout = dict(
    height=600,
    title={
        "text": "Produção de Energia: divisão dos dados em treino e teste", 
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
                dict(count=7, label='1w', step='day', stepmode='backward'),
                dict(count=3, label='3m', step='month', stepmode='backward'),
                dict(count=15, label='test', step='day', stepmode='backward'),
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

fig.add_vline(
    x=split_date,
    line_width=2,
    line_dash="dash",
    line_color="white",
)

fig.add_annotation(
    x=df_test.index[0],
    y=25,
    text='train/test',
    showarrow=True,
    arrowhead=5,
    bgcolor="steelblue",
    bordercolor="#0072B2",
    font=dict(size=14),
    hovertext="Divisão dados de Treino e Teste",
    ax=60,
    ay=-30
)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# Preparar série temporal para previsão (treino e teste)
X_train = df_train[features]
y_train = df_train[[target]]

X_test = df_test[features]
y_test = df_test[[target]]

df_pred = df_test[[target]].copy()
exp_exec = False

if st.button("Iniciar Experimento"):
    with st.spinner("Executando o Experimento..."):
        xgb_base = xgb.XGBRegressor()
        xgb_base.fit(
            X_train,
            y_train,
            eval_set=[(X_train, y_train), (X_test, y_test)],
            verbose=500,
        )

        df_pred.rename(columns={target: "y_true"}, inplace=True)
        df_pred["xgb_pred"] = xgb_base.predict(X_test)

    st.success("Experimento finalizado")
    exp_exec = True

else:
    st.warning("Clique em iniciar experimento.")

if exp_exec:

    st.write("## Modelo XGBoost")

    c1, c2 = st.columns(2)
    with c1:
        st.write("### Dataframe predict")
        st.dataframe(df_pred, use_container_width=True)

    with c2:
        st.write("### Métricas")
        metrics = calculate_metrics(df_pred["y_true"], df_pred["xgb_pred"])
        df_metrics = pd.DataFrame.from_dict(metrics, orient="index")
        st.dataframe(df_metrics, use_container_width=True)

    st.write("")
    st.divider()
    st.write("")

    cols = st.columns(4)
    for col, (key, value) in zip(cols, metrics.items()):
        col.metric(
            label=f"{key.upper()}",
            label_visibility="collapsed",
            value=round(value, 4),
            delta=f"{key.upper()}",
            delta_color="normal"
        )

    # Plotar gráfico de previsão
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
            y=df_pred["xgb_pred"],
            mode='lines',
            line=dict(color="coral"),
            name='predict'
        )
    ]
    layout = dict(
        height=600,
        title={
            "text": "Produção de Energia: previsão com modelo XGBoost", 
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

    st.divider()
    # Importancia das Variaveis (Feature Importance) xgboost

    features_importance = pd.DataFrame(
        data=xgb_base.feature_importances_,
        index=xgb_base.feature_names_in_,
        columns=["importance"],
    )

    total_importance = features_importance["importance"].sum()
    features_importance["percentage"] = (features_importance["importance"] / total_importance) * 100
    sorted_df = features_importance.sort_values(by="percentage", ascending=True)

    st.write("## Importância dos recursos")
    fig = px.bar(
        sorted_df.head(10),
        x="importance",
        y=sorted_df.head(10).index,
        orientation="h",
        color_continuous_scale=px.colors.sequential.Viridis,
        title="Importância dos recursos (Feature Importance)",
        labels={"importance": "Importância (%)", "index": "Variável"},
    )
    st.plotly_chart(fig, use_container_width=True)

    st.download_button(
        "Download Model",
        # data=pickle.dumps(clf),
        # file_name="model.pkl",
    )
 