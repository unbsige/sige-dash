import plotly.express as px
import plotly.graph_objs as go
import streamlit as st

dark_cyan = "#008B8B"
train_color = dark_cyan
test_color = "#1f77b4"
predict_color = '#0072B2'
forecast_color = "#ff7f0e"
error_color = 'rgba(0, 114, 178, 0.2)'  # '#0072B2' with 0.2 opacity
trend_color = '#B23B00'


def plot_go_scatter(df, x, y, title):
    line_width = 2.5
    marker_size = 4

    data = [
        go.Scatter(
            name="Predição",
            x=df.index,
            y=df[y],
            line=dict(color=train_color, width=line_width),
            mode="lines",
            showlegend=False,
            hovertemplate="%{x}: %{y} kWh",
        )
    ]
    figsize = (900, 550)
    layout = dict(
        showlegend=False,
        height=figsize[1],
        yaxis=dict(title="Produção de Energia (kWh)"),
        xaxis=dict(
            title="",
            type='date',
            rangeslider=dict(visible=True),
            rangeselector=dict(
                buttons=[
                    dict(count=1, label='1d', step='day', stepmode='backward'),
                    dict(count=7, label='1w', step='day', stepmode='backward'),
                    dict(count=1, label='1m', step='month', stepmode='backward'),
                    dict(count=3, label='3m', step='month', stepmode='backward'),
                    dict(step='all'),
                ],
                font=dict(size=13),
                bordercolor="#0072B2",
                borderwidth=1,
                activecolor="#0072B2",
            ),
        ),
    )
    fig = go.Figure(data=data, layout=layout)
    st.plotly_chart(fig, use_container_width=True)


def plot_graph_line(df, x, y, title):
    fig = px.line(df, x=x, y=y, template="simple_white", title=f"<b>{title}</b>")
    fig.update_layout(title={"y": 0.9, "x": 0.5, "xanchor": "center", "yanchor": "top", "font": {"size": 20}})
    fig.update_traces(line_width=2.5)
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    fig.update_yaxes(showgrid=True, gridwidth=0.1)
    fig.update_xaxes(title_text="")
    fig.update_yaxes(title_text="Energy Production (kWh)")
    st.plotly_chart(fig, use_container_width=True)


def plot_graph_bar(df, x_column, y_column, title):
    fig = px.bar(
        df,
        x=x_column,
        y=y_column,
        template="simple_white",
        barmode="group",
        title=f"<b>{title}</b>",
        text=y_column,
        hover_name=y_column,
    )
    fig.update_traces(
        marker_color="#A27D4F",
        textposition="outside",
        hovertemplate="%{x}: %{y} kWh"
    )
    fig.update_layout(title={"y": 0.9, "x": 0.5, "xanchor": "center", "yanchor": "top"})
    fig.update_traces(marker_color="#A27D4F")
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    fig.update_yaxes(showgrid=True, gridwidth=0.1)
    fig.update_xaxes(title_text="")
    fig.update_yaxes(title_text="kWh")
    st.plotly_chart(fig, use_container_width=True)
    