import streamlit as st
from plotly import express as px

st.set_page_config(
    page_title="Visualização dos Dados",
    page_icon=":chart_with_upwards_trend:",
    layout="wide",
)
st.title("Visualização dos Dados")
# if "df_prod" not in st.session_state:
#     st.stop()


# ============================================================================================================
tab1, tab2 = st.tabs(["Tab 1", "Tab2"])
tab1.write("this is tab 1")
tab2.write("this is tab 2")

st.title('Counter Example using Callbacks')
if 'count' not in st.session_state:
    st.session_state.count = 0


def increment_counter():
    st.session_state.count += 1


def clear_counter():
    st.session_state.count = 0


st.button('Increment', on_click=increment_counter)
st.write('Count = ', st.session_state.count)
st.button("Clear", on_click=clear_counter)

# ============================================================================================================

st.stop()

df_prod = st.session_state.df_prod
df_rad = st.session_state.df_rad


def plot_graph_line(data, x, y, title):
    fig = px.line(data, x=x, y=y, title=title)
    fig.update_layout(title={"y": 0.9, "x": 0.5, "xanchor": "center", "yanchor": "top"})
    st.plotly_chart(fig, use_container_width=True)


def plot_graph_bar(data, x, y, title):
    fig = px.bar(data, x=x, y=y, title=title)
    fig.update_layout(title={"y": 0.9, "x": 0.5, "xanchor": "center", "yanchor": "top"})
    st.plotly_chart(fig, use_container_width=True)


def plot_graph_pie(data, x, y, title):
    fig = px.pie(data, values=y, names=x, title=title)
    fig.update_layout(title={"y": 0.9, "x": 0.5, "xanchor": "center", "yanchor": "top"})
    st.plotly_chart(fig, use_container_width=True)


def plot_graph_scatter(data, x, y, title):
    fig = px.scatter(data, x=x, y=y, title=title)
    fig.update_layout(title={"y": 0.9, "x": 0.5, "xanchor": "center", "yanchor": "top"})
    st.plotly_chart(fig, use_container_width=True)


def plot_graph_histogram(data, x, y, title):
    fig = px.histogram(data, x=x, y=y, title=title)
    fig.update_layout(title={"y": 0.9, "x": 0.5, "xanchor": "center", "yanchor": "top"})
    st.plotly_chart(fig, use_container_width=True)


def plot_graph_box(data, x, y, title):
    fig = px.box(data, x=x, y=y, title=title)
    fig.update_layout(title={"y": 0.9, "x": 0.5, "xanchor": "center", "yanchor": "top"})
    st.plotly_chart(fig, use_container_width=True)


def plot_graph_area(data, x, y, title):
    fig = px.area(data, x=x, y=y, title=title)
    fig.update_layout(title={"y": 0.9, "x": 0.5, "xanchor": "center", "yanchor": "top"})
    st.plotly_chart(fig, use_container_width=True)


def plot_graph_heatmap(data, x, y, title):
    fig = px.imshow(data, x=x, y=y, title=title)
    fig.update_layout(title={"y": 0.9, "x": 0.5, "xanchor": "center", "yanchor": "top"})
    st.plotly_chart(fig, use_container_width=True)


def plot_graph_violin(data, x, y, title):
    fig = px.violin(data, x=x, y=y, title=title)
    fig.update_layout(title={"y": 0.9, "x": 0.5, "xanchor": "center", "yanchor": "top"})
    st.plotly_chart(fig, use_container_width=True)


def plot_graph(data, x, y, title, graph_type):
    if graph_type == "Bar":
        plot_graph_bar(data, x, y, title)
    elif graph_type == "Line":
        plot_graph_line(data, x, y, title)
    elif graph_type == "Pie":
        plot_graph_pie(data, x, y, title)
    elif graph_type == "Scatter":
        plot_graph_scatter(data, x, y, title)
    elif graph_type == "Histogram":
        plot_graph_histogram(data, x, y, title)
    elif graph_type == "Box":
        plot_graph_box(data, x, y, title)
    elif graph_type == "Area":
        plot_graph_area(data, x, y, title)
    elif graph_type == "Heatmap":
        plot_graph_heatmap(data, x, y, title)
    elif graph_type == "Violin":
        plot_graph_violin(data, x, y, title)
        plot_graph_violin(data, x, y, title)


#  ============================================================================================
st.write(df_prod)

st.write("## Gráficos")
st.sidebar.write("## Filtros")
target = st.sidebar.selectbox("Selecione o alvo", df_prod.columns, key="target_name")
x_column = st.sidebar.selectbox("Selecione o eixo X", df_prod.columns, key="x_name")

plot_graph(df_prod, df_prod.index, target, "Bar", "Bar")
plot_graph(df_prod, df_prod.index, target, "Line", "Line")
# plot_graph(df_prod, df_prod.index, target, "", "Pie")
plot_graph(df_prod, df_prod.index, target, "Scatter", "Scatter")
plot_graph(df_prod, df_prod.index, target, "Histogram", "Histogram")
plot_graph(df_prod, df_prod.index, target, "Box", "Box")
plot_graph(df_prod, df_prod.index, target, "Area", "Area")
# plot_graph(df_prod, df_prod.index, target, "Heatmap", "Heatmap")
plot_graph(df_prod, df_prod.index, target, "Violin", "Violin")
#  ============================================================================================
