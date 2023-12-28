import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import xgboost as xgb

from config.settings import (
    CYCLIC_FEATURES,
    END_DATE,
    IRRADIATION_FEATURES,
    LAG_FEATURES,
    RADIAL_FEATURES,
    SINCE_FEATURES,
    SPLIT_DATE,
    START_DATE,
    TARGET_AGG,
    TARGETS,
    TIME_FEATURES,
    WEATHER_FEATURES,
    WINDOWS_FEATURES,
)
from feature_utils import create_features
from load_data import load_data
from metric_utils import calculate_forecast_accuracy


def multiselect_with_all(title, options):
    all_selected = st.sidebar.checkbox(f"Selecionar Todos {title}", key=title)
    if all_selected:
        selected_options = st.sidebar.multiselect(title, options, options, key=title)
    else:
        selected_options = st.sidebar.multiselect(title, options, key=title)
    return selected_options


def reset_feature_selections():
    st.session_state['reset_selections'] = True
    st.write("Resetando seleções...")
    st.rerun()


# ==================================================================================================================
st.set_page_config(
    page_title="Machine Learning",
    page_icon=":chart_with_upwards_trend:",
    layout="wide",
)

if "df_prod" not in st.session_state:
    load_data()

st.title("Machine Learning")
st.subheader("Conjuntos de dados")

df_prod = st.session_state.df_prod
df_rad = st.session_state.df_rad
df_wth = st.session_state.df_wth

with st.expander("⚡ :green[Dados de Produção de energia]"):
    st.dataframe(df_prod[TARGETS], use_container_width=True)

with st.expander("☀️ :green[Dados Irradiação solar]"):
    st.dataframe(df_rad, use_container_width=True)

with st.expander("☁️ :green[Dados Meteorológicos]"):
    st.dataframe(df_wth, use_container_width=True)

# ==================================================================================================================
st.write(" ")
st.divider()

st.sidebar.subheader("1. Configuração dos Dados")
st.sidebar.subheader("1. Preparar conjunto de dados")

st.subheader("1. Seleção da coluna target (variável dependente)")
cols = st.columns(3)
with cols[0]:
    target_cols = TARGETS + TARGET_AGG
    target = st.selectbox(
        "Selecione coluna target", 
        options=target_cols,
        index=None,
        placeholder="Selecionar coluna para prever",
    )

if not target:
    st.warning("🔒 Selecione a coluna de target")
    st.stop()

df_prod = df_prod[[target]].copy()
df_prod = create_features(df_prod, col=target)

st.subheader("2. Seleção de recursos")
with st.expander("1. Seleção de recursos"):
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("##### A) Recursos internos", unsafe_allow_html=True)

    feature_sets = [
        ("Recursos de tempo", TIME_FEATURES),
        ("Recursos cíclicos", CYCLIC_FEATURES),
        ("Recursos de tempo desde", SINCE_FEATURES),
        ("Recursos radiais", RADIAL_FEATURES),
        ("Recursos de lag", LAG_FEATURES),
        ("Recursos de janela", WINDOWS_FEATURES),
    ]

    cols = st.columns(3)
    features = []
    for idx, (title, options) in enumerate(feature_sets):
        with cols[idx % len(cols)]:
            selected_features = st.multiselect(title, options=["todos"] + options)
            features.extend(options if "todos" in selected_features else selected_features)
            # st.session_state[title] = features

    data = df_prod.copy()
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("##### B) Recursos externos", unsafe_allow_html=True)
    c1, c2 = st.columns(2)

    use_irradiation_data = c1.checkbox("Utilizar dados de irradiação solar")
    use_weather_data = c2.checkbox("Utilizar dados meteorológicos")

    if use_irradiation_data:
        data = pd.concat([df_prod, df_rad], axis=1)
        irradiation_features = c1.multiselect("Recursos de irradiação", options=["todos"] + IRRADIATION_FEATURES)
        features.extend(IRRADIATION_FEATURES if "todos" in irradiation_features else irradiation_features)

    if use_weather_data:
        data = pd.concat([data, df_wth], axis=1)
        weather_features = c2.multiselect("Recursos meteorológicos", options=["todos"] + WEATHER_FEATURES)
        features.extend(WEATHER_FEATURES if "todos" in weather_features else weather_features)

# ------------------------------------------------------------------------------------------------------------------
    st.divider()

    if features:
        c1, c2 = st.columns([2, 8])
        with c1:
            st.markdown("##### *Target (Y)*", unsafe_allow_html=True)
            st.dataframe(data[target])

        with c2:
            st.markdown("##### *Features (X)* - Variáveis Independentes", unsafe_allow_html=True)
            st.dataframe(data[features], hide_index=True)

if not target or not features:
    st.warning("🔒 Selecione a coluna de target e no mínimo uma coluna de recurso")
    st.stop()

# ==================================================================================================================
df_ml = data[features + [target]].copy()
df_base = df_ml.loc[START_DATE:END_DATE].copy()
df_eval = df_ml.loc[END_DATE:].copy()


st.divider()
st.sidebar.divider()
# st.sidebar.subheader("2. Selecione a data de corte do dataset de teste")
# split_date = st.sidebar.date_input("Data de corte", value=SPLIT_DATE)

st.subheader("2. Dividir conjunto de dados em treino e teste")
with st.expander("2. Dividir dataframe em treino e teste"):
    st.subheader("Selecione a data de corte do dataset de teste")

    split_date = st.date_input("Data de corte", value=SPLIT_DATE)
    df_train = df_base.loc[:split_date]
    df_test = df_base.loc[split_date:]

    graph_tab, table_tab = st.tabs(["Gráfico", "Tabela"])

    with graph_tab:
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

    with table_tab:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Conjunto de dados de treinamento *(df_train)*", unsafe_allow_html=True)
            st.caption("Conjunto de dados de treinamento")
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

        with c2:
            st.markdown("#### Conjunto de dados de teste *(df_test)*", unsafe_allow_html=True)
            st.caption("Conjunto de dados de teste")
            start_date = df_test.index.min().strftime('%d-%m-%Y %H:%M:%S')
            end_date = df_test.index.max().strftime('%d-%m-%Y %H:%M:%S')
            n_rows = df_test.shape[0]

            c21, c22 = st.columns(2)
            c21.metric(
                label="Data de inicio",
                label_visibility="collapsed",
                value=start_date,
                delta="Inicio do dataset de teste",
                delta_color="normal",
            )
            c22.metric(
                label="Data de fim",
                label_visibility="collapsed",
                value=end_date,
                delta="Final do dataset de teste",
                delta_color="normal",
            )
            st.dataframe(df_test, use_container_width=True)
            st.write(f"Numero de linhas: {n_rows}")


st.divider()

# Preparar série temporal para previsão (treino e teste)
X_train = df_train[features]
y_train = df_train[[target]]

X_test = df_test[features]
y_test = df_test[[target]]

df_pred = df_test[[target]].copy()
exp_exec = False

if st.button("🧪  Iniciar Experimento"):
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
        metrics = calculate_forecast_accuracy(df_pred["y_true"], df_pred["xgb_pred"], y_train)
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

    # st.download_button(
    #     "Download Model",
        # data=pickle.dumps(clf),
        # file_name="model.pkl",
    # )
 