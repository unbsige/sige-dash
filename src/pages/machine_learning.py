import pandas as pd

# import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import xgboost as xgb

from src.config.settings import END_DATE, FEATURES, SPLIT_DATE, START_DATE, TARGET
from src.metric_utils import calculate_metrics

st.set_page_config(
    page_title="Machine Learning",
    page_icon=":chart_with_upwards_trend:",
    layout="wide",
)

st.title("Visualização dos Dados")
st.subheader("Dataframe Geral")
df = st.session_state["df"]
st.dataframe(df, use_container_width=True)

cols_ml = [TARGET] + FEATURES
df = df.rename(columns={"avg_ldtea": TARGET})
df = df[cols_ml]

df_base = df.loc[START_DATE:END_DATE].copy()
df_eval = df.loc[END_DATE:].copy()

df_train = df_base.loc[:SPLIT_DATE]
df_test = df_base.loc[SPLIT_DATE:]

st.subheader("Dataframe para projeto de ML")
st.write("###### Selecionado colunas de recursos e avg_ldtea como target")

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
        y=df_train[TARGET],
        mode='lines',
        line=dict(color="darkcyan"),
        name='train set'
    ),

    go.Scatter(
        x=df_test.index,
        y=df_test[TARGET],
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
    x=SPLIT_DATE,
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
st.divider()

# Preparar série temporal para previsão (treino e teste)
X_train = df_train[FEATURES]
y_train = df_train[[TARGET]]

X_test = df_test[FEATURES]
y_test = df_test[[TARGET]]

df_pred = df_test[[TARGET]].copy()
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

        df_pred.rename(columns={TARGET: "y_true"}, inplace=True)
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
