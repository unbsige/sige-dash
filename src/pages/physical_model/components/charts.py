from datetime import datetime

import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots


def create_preview_chart(df_data, start_date, end_date):
    fig = make_subplots(
        rows=2,
        cols=1,
        subplot_titles=["Irradiância Solar Global Tilted (GTI)", "Temperatura do Ar"],
        shared_xaxes=True,
        vertical_spacing=0.15,
        specs=[[{"secondary_y": False}], [{"secondary_y": False}]],
    )

    fig.add_trace(
        go.Scatter(
            x=df_data.index,
            y=df_data["gti"],
            mode="lines",
            line={"color": "#FF6B35", "width": 1.5},
            name="GTI (W/m²)",
            hovertemplate="<b>GTI:</b> %{y:.1f} W/m²<br><b>Data:</b> %{x}<extra></extra>",
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=df_data.index,
            y=df_data["air_temp"],
            mode="lines",
            line={"color": "#1E88E5", "width": 1.5},
            name="Temperatura (°C)",
            hovertemplate="<b>Temperatura:</b> %{y:.1f} °C<br><b>Data:</b> %{x}<extra></extra>",
        ),
        row=2,
        col=1,
    )

    fig.update_layout(
        height=500,
        title={
            "text": f"Preview dos Dados Meteorológicos ({start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')})",
            "y": 0.95,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
            "font": {"size": 18, "family": "Arial, sans-serif"},
        },
        margin=dict(l=60, r=20, t=80, b=60),
        plot_bgcolor="white",
        paper_bgcolor="white",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font={"size": 12}),
        hovermode="x unified",
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor="#E5E5E5",
        gridwidth=1,
        showline=True,
        linecolor="#CCCCCC",
        title="",
        tickformat="%d/%m\n%H:%M",
        row=2,
        col=1,
    )

    fig.update_xaxes(showgrid=True, gridcolor="#E5E5E5", gridwidth=1, showline=True, linecolor="#CCCCCC", row=1, col=1)

    fig.update_yaxes(
        title="Irradiância (W/m²)",
        showgrid=True,
        linecolor="#CCCCCC",
        tickformat=".0f",
        row=1,
        col=1,
    )

    fig.update_yaxes(
        title="Temperatura (°C)",
        showline=True,
        linecolor="#CCCCCC",
        tickformat=".1f",
        row=2,
        col=1,
    )

    fig.update_layout(
        xaxis2=dict(
            rangeslider=dict(visible=True, thickness=0.05),
            rangeselector=dict(
                buttons=[
                    {"count": 1, "label": "1D", "step": "day", "stepmode": "backward"},
                    {"count": 7, "label": "7D", "step": "day", "stepmode": "backward"},
                    {"count": 30, "label": "30D", "step": "day", "stepmode": "backward"},
                    {"step": "all", "label": "Todos"},
                ],
                font={"size": 11},
                bgcolor="#F8F9FA",
                bordercolor="#DEE2E6",
                borderwidth=1,
                activecolor="#007BFF",
                x=0,
                y=1.15,
            ),
        )
    )

    return fig


def show_meteorological_preview(df_data, start_date, end_date):
    with st.expander("📊 Preview dos Dados Meteorológicos", expanded=True):
        graph_tab, stats_tab, table_tab = st.tabs(["📈 Gráfico", "📋 Estatísticas", "📋 Dados"])

        with graph_tab:
            fig_preview = create_preview_chart(df_data, start_date, end_date)
            st.plotly_chart(fig_preview, use_container_width=True)

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "GTI Máximo",
                    f"{df_data['gti'].max():.0f} W/m²",
                    delta=f"Média: {df_data['gti'].mean():.0f}",
                )

            with col2:
                st.metric(
                    "GTI Mínimo",
                    f"{df_data['gti'].min():.0f} W/m²",
                    delta=f"Desvio: {df_data['gti'].std():.0f}",
                )

            with col3:
                st.metric(
                    "Temp. Máxima",
                    f"{df_data['air_temp'].max():.1f} °C",
                    delta=f"Média: {df_data['air_temp'].mean():.1f}",
                )

            with col4:
                st.metric(
                    "Temp. Mínima",
                    f"{df_data['air_temp'].min():.1f} °C",
                    delta=f"Desvio: {df_data['air_temp'].std():.1f}",
                )

        with stats_tab:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### 🌞 Estatísticas da Irradiância GTI")
                stats_gti = df_data["gti"].describe()
                st.dataframe(stats_gti.to_frame().T.round(2), use_container_width=True)

                max_gti_date = df_data["gti"].idxmax()
                st.info(
                    f"**Maior irradiância:** {df_data['gti'].max():.0f} W/m² em {max_gti_date.strftime('%d/%m/%Y às %H:%M')}"
                )

            with col2:
                st.markdown("#### 🌡️ Estatísticas da Temperatura")
                stats_temp = df_data["air_temp"].describe()
                st.dataframe(stats_temp.to_frame().T.round(2), use_container_width=True)
                max_temp_date = df_data["air_temp"].idxmax()
                st.info(
                    f"**Maior temperatura:** {df_data['air_temp'].max():.1f} °C em {max_temp_date.strftime('%d/%m/%Y às %H:%M')}"
                )

        with table_tab:
            st.markdown("#### 📋 Amostra dos Dados")
            st.caption(
                f"Período: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')} | Total de registros: {len(df_data):,}"
            )

            # Mostrar primeiros e últimos registros
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**🔝 Primeiros 10 registros**")
                st.dataframe(df_data.head(10), use_container_width=True)

            with col2:
                st.markdown("**🔚 Últimos 10 registros**")
                st.dataframe(df_data.tail(10), use_container_width=True)


def display_simulation_results(results):
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        energy_total = results["ac_power_kw_est"].sum()
        st.metric("Energia Total", f"{energy_total:.2f} KWh")

    with col2:
        capacity_factor = (energy_total * 1000) / (results["dc_power_kw"].max() * len(results) / (365 * 24 / 5)) * 100
        st.metric("Fator de Capacidade", f"{capacity_factor:.1f}%")

    with col3:
        avg_efficiency = results["inv_efficiency"].mean()
        st.metric("Eficiência Média Inversor", f"{avg_efficiency:.1%}")

    with col4:
        avg_dc_loss = 1 - results["cpdc"].mean()
        st.metric("Perdas DC Médias", f"{avg_dc_loss:.1%}")


def create_results_chart(results):
    """Cria gráfico de resultados da simulação."""
    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=[
            "Potência ao Longo do Tempo",
            "Eficiência do Inversor",
            "Perdas DC vs Irradiância",
            "Correlação GTI vs AC",
        ],
        specs=[[{"colspan": 2}, None], [{}, {}]],
        vertical_spacing=0.12,
    )

    # Potência vs tempo (gráfico principal)
    fig.add_trace(
        go.Scatter(
            x=results.index,
            y=results["dc_power_kw"],
            name="DC Power",
            line=dict(color="#ff7f0e", width=1),
            opacity=0.7,
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=results.index, y=results["ac_power_kw_est"], name="AC Power", line=dict(color="#1f77b4", width=1.5)
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=results["dc_power_kw"],
            y=results["inv_efficiency"],
            mode="markers",
            name="Eficiência",
            marker=dict(color="#2ca02c", size=3, opacity=0.6),
            showlegend=False,
        ),
        row=2,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=results["gti"],
            y=results["cpdc"],
            mode="markers",
            name="CPdc",
            marker=dict(color="#d62728", size=3, opacity=0.6),
            showlegend=False,
        ),
        row=2,
        col=2,
    )

    fig.update_layout(
        height=500,
        margin=dict(l=0, r=0, t=40, b=0),
        plot_bgcolor="white",
        paper_bgcolor="white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    fig.update_xaxes(showgrid=True, gridcolor="#f0f0f0")
    fig.update_yaxes(showgrid=True, gridcolor="#f0f0f0")

    return fig


def create_simulation_plots(results):
    """Cria gráficos dos resultados."""

    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=[
            "Potência vs Tempo",
            "Eficiência do Inversor",
            "Perdas DC",
            "Correlação Irradiância vs Potência",
        ],
        specs=[[{"secondary_y": True}, {"secondary_y": False}], [{"secondary_y": False}, {"secondary_y": False}]],
    )

    fig.add_trace(
        go.Scatter(
            x=results.index,
            y=results["dc_power_kw"],
            name="DC Power",
            line=dict(color="orange"),
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=results.index,
            y=results["ac_power_kw_est"],
            name="AC Power Est",
            line=dict(color="blue"),
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=results["dc_power_kw"],
            y=results["inv_efficiency"],
            mode="markers",
            name="Eficiência",
            opacity=0.6,
        ),
        row=1,
        col=2,
    )

    fig.add_trace(
        go.Scatter(
            x=results["gti"],
            y=results["cpdc"],
            mode="markers",
            name="CPdc",
            opacity=0.6,
            marker=dict(color="red"),
        ),
        row=2,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=results["gti"], y=results["ac_power_kw_est"], mode="markers", name="GTI vs AC Power", opacity=0.4
        ),
        row=2,
        col=2,
    )

    fig.update_layout(height=600, showlegend=True)
    st.plotly_chart(fig, width="stretch")
