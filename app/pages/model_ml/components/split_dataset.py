import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from config.settings import END_DATE, SPLIT_DATE_EVAL, START_DATE


def split_train_test(df_features, target):
    st.subheader("Divisão dos Dados")

    start_date = pd.to_datetime(START_DATE)
    end_date = pd.to_datetime(END_DATE)
    split_date_eval = pd.to_datetime(SPLIT_DATE_EVAL)

    cols = st.columns(4)
    with cols[0]:
        start_date_sel = st.date_input("Data Inicial", value=start_date)
    with cols[1]:
        split_date = st.date_input("Data de corte para Teste", value=split_date_eval)

    start_date_sel = pd.to_datetime(start_date_sel)
    split_date = pd.to_datetime(split_date)

    if split_date > end_date:
        st.error("Data de corte para teste não pode ser maior que a data final")
        return None
    elif split_date < start_date:
        st.error("Data de corte para teste não pode ser menor que a data inicial")
        return None

    df_train = df_features.loc[start_date_sel:split_date].copy()
    df_test = df_features.loc[split_date:end_date].copy()

    datasets = {
        "df_features": df_features,
        "df_train": df_train,
        "df_test": df_test,
    }

    show_split_graph(df_train, df_test, target, split_date)
    return datasets


def show_split_graph(df_train, df_test, target, split_date):
    with st.expander("2. Dividir dataframe em treino e teste", expanded=True):

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

# ------------------------------------------------------------------------------------------

    # show_split_graph(df_train, df_test, split_test_data)

    # X_train = df_train[features]
    # y_train = df_train[[target]]

    # X_test = df_test[features]
    # y_test = df_test[[target]]

    # df_pred = df_test[[target]].copy()
    # exp_exec = False
