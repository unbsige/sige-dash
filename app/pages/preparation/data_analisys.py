import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Analise dos Dados",
    page_icon=":chart_with_upwards_trend:",
    layout="wide",
)
st.title("Analise dos Dados")

# if "df_prod" not in st.session_state:
#     st.stop()

df_prod = st.session_state.df_prod
df_rad = st.session_state.df_rad
# ============================================================================================================
LAT = -15.9895
LON = -48.0444

data = pd.DataFrame({
    'lat': [-15.98895, -15.99051, -15.98955],
    'lon': [-48.04485, -48.04425, -48.04545],
    'name': ['UAC', 'LDTEA', 'UED'],
    'power': [5000, 5000, 5000]
})

# Criar um mapa interativo com Plotly
fig = px.scatter_mapbox(
    data,
    lat="lat",
    lon="lon",
    hover_name="name",
    hover_data=["power"],
    template="plotly_dark",
    color_discrete_sequence=["red"],
    zoom=17,
    height=500,
    # width=1440,
    size="power",
    size_max=10,
    title="Potência instalada",
    center={"lat": LAT, "lon": LON},

)
fig.update_layout(
    autosize=True,
    mapbox_style="open-street-map",
    margin={"r": 0, "t": 0, "l": 0, "b": 0}
)
st.plotly_chart(fig, use_container_width=True)

# ============================================================================================================
fig.add_trace(go.Scattermapbox(
    lat=data['lat'].tolist() + [data['lat'].tolist()[0]],  # Adiciona o primeiro ponto ao final para fechar o polígono
    lon=data['lon'].tolist() + [data['lon'].tolist()[0]],  # Adiciona o primeiro ponto ao final para fechar o polígono
    mode='lines',
    fill='toself',  # Isso preenche a área dentro do polígono
    fillcolor='rgba(255, 0, 0, 0.2)',  # Define a cor e a transparência do preenchimento
    line=dict(width=0),
))

st.plotly_chart(fig, use_container_width=True)
# ============================================================================================================

st.stop()


def sort_data(data):
    sort_col = st.selectbox("Select column to sort by", data.columns)
    return data.sort_values(by=sort_col)


def remove_duplicates(data):
    st.write("### Remove Duplicates")
    columns = st.multiselect(
        "Select columns for identifying duplicates", options=data.columns
    )

    if columns:
        data.drop_duplicates(subset=columns, inplace=True)
        st.write("Duplicates removed successfully!")


def show_data(data):
    st.write("Dataset")
    st.write(data)

    st.write("Standard Deviation")
    st.write(data.std(numeric_only=True))

    st.write("Missing Values")
    st.write(data.isnull().sum())

    st.write("Missing Percentage")
    st.write(data.isna().mean().mul(100))

    st.write("Unique Values")
    st.write(data.nunique())

    st.write("Number of rows")
    st.write(data.shape[0])
    st.write("Number of columns")
    st.write(data.shape[1])

    st.write("Data Correlation")
    st.write(data.corr(numeric_only=True))

    st.write("Data correlation")
    st.write(
        data.corr(numeric_only=True).style.background_gradient(
            cmap="RdBu", vmin=-1, vmax=1
        )
    )


container = st.container()
col1, col2 = st.columns(2)

st.sidebar.subheader("Filtros")

with container:
    st.write("Intervalo:", df_prod.index.min().date(), df_prod.index.max().date())
    st.write("Tamanho do dataset:", df_prod.shape)
    st.write("Dados nulos:", df_prod.isna().sum().sum())
    st.write("Dados duplicados:", df_prod.duplicated().sum())

    st.write(df_prod.head())

with col1:
    all_columns = df_prod.columns.to_list()
    st.write("Colunas do dataframe:", all_columns)

with col2:
    df_types = df_prod.dtypes.reset_index().rename(columns={"index": "coluna", 0: "tipo"})
    df_types["tipo"] = df_types["tipo"].astype(str)
    df_types.set_index("coluna", inplace=True)
    st.write("Tipos dos dados", df_types.to_dict()["tipo"])


st.subheader("Selecione as colunas para criar o dataset para analise")
selected_columns = st.sidebar.multiselect("Select columns", options=all_columns)

if selected_columns:
    st.write("### Sub DataFrame")
    c1, c2 = st.columns(2)
    sub_df = df_prod[selected_columns]

    st.write(f"Linhas: {sub_df.shape[0]}")
    st.write(f"Colunas: {sub_df.shape[1]}")
    with c1:
        st.write("### Head")
        st.write(sub_df.head())

    with c2:
        st.write("### Tail")
        st.write(sub_df.tail())

    st.markdown("---")
    st.write("### Seção de estatísticas e informações")
    # c1, c2, c3, c4 = st.columns(4)
    c1, c2, c3, c4 = st.columns([1, 1, 1, 2])

    with c1:
        st.write("Desvio padrão (std)")
        st.write(sub_df.std(numeric_only=True))

    with c2:
        st.write("Valores ausentes (missing values)")
        df_stat = sub_df.isnull().sum()
        # Adicionar percentual de valores ausentes

        st.write(df_stat)

    with c3:
        st.write("Porcentagem de valores ausentes")
        st.write(sub_df.isna().mean().mul(100))

    with c4:
        st.write("Correlação entre as colunas")
        st.write(sub_df.corr().style.background_gradient(cmap="RdBu", vmin=-1, vmax=1))
else:
    st.warning("Selecione no minimo uma coluna.")
