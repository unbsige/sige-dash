import streamlit as st

st.set_page_config(
    page_title="Analise dos Dados",
    page_icon=":chart_with_upwards_trend:",
    layout="wide",
)
st.title("Analise dos Dados")

if "df_prod" not in st.session_state:
    st.stop()

df_prod = st.session_state.df_prod
df_rad = st.session_state.df_rad

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
