import streamlit as st

st.set_page_config(page_title="Analise dos Dados", page_icon=":chart_with_upwards_trend:", layout="wide",)
st.title("Analise dos Dados")
df = st.session_state.df
st.write(df)
