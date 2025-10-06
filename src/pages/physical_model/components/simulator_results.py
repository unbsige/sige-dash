import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots


def render_simulation_results(results, df_pred, metrics, selected_plant_key):
    """Renderiza resultados da simulação de forma organizada e minimalista"""

    st.markdown("---")
    st.markdown("### Resultados da Simulação NBR 16274")

    render_performance_metrics(metrics)
    render_comparison_charts(df_pred, results)
    render_detailed_analysis(results, df_pred)
    render_download_section(results, selected_plant_key)


def render_performance_metrics(metrics):
    st.markdown("#### Métricas de Precisão")

    mae = metrics.get("mae", 0)
    nmae = metrics.get("nmae", 0)
    rmse = metrics.get("rmse", 0)
    nrmse = metrics.get("nrmse", 0)
    mape = metrics.get("mape", 0)
    r2 = metrics.get("r2", 0)

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        st.markdown(
            f"""
            <div style="
                background: white;
                border: 1px solid #E0E0E0;
                border-left: 4px solid #4CAF50;
                border-radius: 8px;
                padding: 15px;
                text-align: center;
            ">
                <div style="color: #4CAF50; font-size: 1.4rem; font-weight: 600;">{mae:.2f}</div>
                <div style="color: #666; font-size: 0.9rem;">MAE (kW)</div>
                <div style="color: #999; font-size: 0.8rem;">Erro médio absoluto</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div style="
                background: white;
                border: 1px solid #E0E0E0;
                border-left: 4px solid #2196F3;
                border-radius: 8px;
                padding: 15px;
                text-align: center;
            ">
                <div style="color: #2196F3; font-size: 1.4rem; font-weight: 600;">{rmse:.2f}</div>
                <div style="color: #666; font-size: 0.9rem;">RMSE (kW)</div>
                <div style="color: #999; font-size: 0.8rem;">Raiz do erro quadrático</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        mape_color = "#4CAF50" if mape < 10 else "#FF9800" if mape < 20 else "#F44336"
        st.markdown(
            f"""
            <div style="
                background: white;
                border: 1px solid #E0E0E0;
                border-left: 4px solid {mape_color};
                border-radius: 8px;
                padding: 15px;
                text-align: center;
            ">
                <div style="color: {mape_color}; font-size: 1.4rem; font-weight: 600;">{mape:.1f}%</div>
                <div style="color: #666; font-size: 0.9rem;">MAPE</div>
                <div style="color: #999; font-size: 0.8rem;">Erro percentual médio</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col4:
        r2_color = "#4CAF50" if r2 > 0.9 else "#FF9800" if r2 > 0.8 else "#F44336"
        st.markdown(
            f"""
            <div style="
                background: white;
                border: 1px solid #E0E0E0;
                border-left: 4px solid {r2_color};
                border-radius: 8px;
                padding: 15px;
                text-align: center;
            ">
                <div style="color: {r2_color}; font-size: 1.4rem; font-weight: 600;">{r2:.3f}</div>
                <div style="color: #666; font-size: 0.9rem;">R²</div>
                <div style="color: #999; font-size: 0.8rem;">Coeficiente determinação</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col5:
        nmae_color = "#4CAF50" if nmae < 10 else "#FF9800" if nmae < 20 else "#F44336"
        st.markdown(
            f"""
            <div style="
                background: white;
                border: 1px solid #E0E0E0;
                border-left: 4px solid {nmae_color};
                border-radius: 8px;
                padding: 15px;
                text-align: center;
            ">
                <div style="color: {nmae_color}; font-size: 1.4rem; font-weight: 600;">{nmae:.1f}%</div>
                <div style="color: #666; font-size: 0.9rem;">NMAE</div>
                <div style="color: #999; font-size: 0.8rem;">Erro médio absoluto normalizado</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col6:
        nrmse_color = "#4CAF50" if nrmse < 10 else "#FF9800" if nrmse < 20 else "#F44336"
        st.markdown(
            f"""
            <div style="
                background: white;
                border: 1px solid #E0E0E0;
                border-left: 4px solid {nrmse_color};
                border-radius: 8px;
                padding: 15px;
                text-align: center;
            ">
                <div style="color: {nrmse_color}; font-size: 1.4rem; font-weight: 600;">{nrmse:.1f}%</div>
                <div style="color: #666; font-size: 0.9rem;">NRMSE</div>
                <div style="color: #999; font-size: 0.8rem;">Raiz do erro quadrático norm.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")
    render_metrics_interpretation(mae, rmse, mape, r2, nmae, nrmse)


def render_metrics_interpretation(mae, rmse, mape, r2, nmae, nrmse):
    col1, divider, col2 = st.columns([1, 0.3, 2])

    with col1:
        st.markdown("**Avaliação do Modelo:**")

        if r2 > 0.95 and nmae < 10:  # R² > 95% e NMAE < 10%
            quality = "Excelente"
            quality_color = "#4CAF50"
            quality_icon = "🟢"
            quality_desc = "Modelo altamente preciso"
        elif r2 > 0.90 and nmae < 15:  # R² > 90% e NMAE < 15%
            quality = "Muito Boa"
            quality_color = "#8BC34A"
            quality_icon = "🟢"
            quality_desc = "Modelo confiável"
        elif r2 > 0.85 and nmae < 20:  # R² > 85% e NMAE < 20%
            quality = "Boa"
            quality_color = "#FF9800"
            quality_icon = "🟡"
            quality_desc = "Modelo adequado"
        elif r2 > 0.70 and nmae < 25:  # R² > 70% e NMAE < 25%
            quality = "Aceitável"
            quality_color = "#FF9800"
            quality_icon = "🟡"
            quality_desc = "Modelo precisa calibração"
        else:
            quality = "Inadequado"
            quality_color = "#F44336"
            quality_icon = "🔴"
            quality_desc = "Modelo necessita revisão"

        st.markdown(
            f"""
            <div style="
                background: white;
                border: 2px solid {quality_color};
                border-radius: 8px;
                padding: 20px;
                text-align: center;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            ">
                <div style="color: {quality_color}; font-size: 1.3rem; font-weight: 600; margin-bottom: 8px;">
                    {quality_icon} {quality}
                </div>
                <div style="color: #666; font-size: 0.9rem;">
                    {quality_desc}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown("**Interpretação Detalhada:**")

        interpretations = []
        if r2 > 0.95:
            interpretations.append("• **R² > 0.95**: Correlação excelente com dados reais")
        elif r2 > 0.90:
            interpretations.append("• **R² > 0.90**: Correlação muito boa")
        elif r2 > 0.85:
            interpretations.append("• **R² > 0.85**: Correlação adequada")
        elif r2 > 0.75:
            interpretations.append("• **R² > 0.75**: Correlação moderada")
        else:
            interpretations.append("• **R² < 0.75**: Correlação insuficiente - revisar modelo")

        if nmae < 0.10:
            interpretations.append("• **NMAE < 10%**: Erro muito baixo - precisão excelente")
        elif nmae < 0.15:
            interpretations.append("• **NMAE < 15%**: Erro baixo - precisão muito boa")
        elif nmae < 0.20:
            interpretations.append("• **NMAE < 20%**: Erro moderado - precisão adequada")
        elif nmae < 0.30:
            interpretations.append("• **NMAE < 30%**: Erro alto - modelo precisa ajustes")
        else:
            interpretations.append("• **NMAE > 30%**: Erro muito alto - revisar parâmetros")

        if mae < 5:
            interpretations.append(f"• **MAE = {mae:.2f} kW**: Erro prático muito baixo")
        elif mae < 10:
            interpretations.append(f"• **MAE = {mae:.2f} kW**: Erro prático aceitável")
        elif mae < 20:
            interpretations.append(f"• **MAE = {mae:.2f} kW**: Erro prático moderado")
        else:
            interpretations.append(f"• **MAE = {mae:.2f} kW**: Erro prático alto")

        if (r2 > 0.90 and nmae < 0.15) and (r2 - nmae > 0.75):
            interpretations.append("• **Consistência**: Métricas indicam modelo confiável")
        elif abs(r2 - (1 - nmae)) > 0.3:
            interpretations.append("• **Atenção**: Métricas inconsistentes - verificar dados")

        for interpretation in interpretations:
            st.markdown(interpretation)

        st.markdown("**Recomendações:**")
        if quality in ["Inadequado", "Aceitável"]:
            st.markdown("• Revisar parâmetros de entrada (NOCT, coeficientes)")
            st.markdown("• Verificar qualidade dos dados meteorológicos")
            st.markdown("• Considerar calibração específica da planta")
        elif quality in ["Boa", "Muito Boa"]:
            st.markdown("• Modelo adequado para previsões operacionais")
            st.markdown("• Monitorar performance periodicamente")
        else:
            st.markdown("• Modelo altamente confiável para todas as aplicações")
            st.markdown("• Validar periodicamente com novos dados")

    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()


def render_comparison_charts(df_pred, results):
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df_pred.index,
            y=df_pred["y_true"],
            mode="lines",
            name="Real",
            line=dict(color="#2196F3", width=2),
            opacity=0.8,
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df_pred.index,
            y=df_pred["y_pred"],
            mode="lines",
            name="NBR 16274",
            line=dict(color="#FF9800", width=2),
            opacity=0.8,
        )
    )

    fig.update_layout(
        xaxis=dict(title="Período", showgrid=True, gridcolor="rgba(0,0,0,0.1)"),
        yaxis=dict(title="Potência (kW)", showgrid=True, gridcolor="rgba(0,0,0,0.1)"),
        plot_bgcolor="white",
        paper_bgcolor="rgba(0,0,0,0)",
        height=400,
        margin=dict(t=20, b=40, l=50, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        hovermode="x unified",
    )

    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Dispersão Real vs Simulado**")
        fig_scatter = create_scatter_plot(df_pred)
        st.plotly_chart(fig_scatter, width="stretch", config={"displayModeBar": False})

    with col2:
        st.markdown("**Distribuição dos Erros**")
        fig_hist = create_error_histogram(df_pred)
        st.plotly_chart(fig_hist, width="stretch", config={"displayModeBar": False})


def create_scatter_plot(df_pred):
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df_pred["y_true"],
            y=df_pred["y_pred"],
            mode="markers",
            marker=dict(color="#2196F3", opacity=0.6, size=4),
            name="Dados",
            hovertemplate="Real: %{x:.2f} kW<br>Simulado: %{y:.2f} kW<extra></extra>",
        )
    )

    max_val = max(df_pred["y_true"].max(), df_pred["y_pred"].max())
    fig.add_trace(
        go.Scatter(
            x=[0, max_val],
            y=[0, max_val],
            mode="lines",
            line=dict(color="red", dash="dash", width=2),
            name="Linha ideal",
            showlegend=False,
        )
    )

    fig.update_layout(
        xaxis=dict(title="Real (kW)"),
        yaxis=dict(title="Simulado (kW)"),
        plot_bgcolor="white",
        height=300,
        margin=dict(t=20, b=40, l=50, r=20),
    )

    return fig


def create_error_histogram(df_pred):
    errors = df_pred["y_pred"] - df_pred["y_true"]

    fig = go.Figure()

    fig.add_trace(go.Histogram(x=errors, nbinsx=30, marker=dict(color="#FF9800", opacity=0.7), name="Erros"))

    fig.update_layout(
        xaxis=dict(title="Erro (kW)"),
        yaxis=dict(title="Frequência"),
        plot_bgcolor="white",
        height=300,
        margin=dict(t=20, b=40, l=50, r=20),
        showlegend=False,
    )

    return fig


def render_detailed_analysis(results, df_pred):
    st.markdown("---")

    col1, col2 = st.columns([1, 1])

    with col1:
        with st.expander("📊 Estatísticas Detalhadas"):
            stats_data = {
                "Métrica": [
                    "Média Real",
                    "Média Simulada",
                    "Desvio Padrão Real",
                    "Desvio Padrão Simulado",
                    "Correlação",
                    "Bias médio",
                    "Erro máximo",
                    "Erro mínimo",
                ],
                "Valor": [
                    f"{df_pred['y_true'].mean():.2f} kW",
                    f"{df_pred['y_pred'].mean():.2f} kW",
                    f"{df_pred['y_true'].std():.2f} kW",
                    f"{df_pred['y_pred'].std():.2f} kW",
                    f"{df_pred['y_true'].corr(df_pred['y_pred']):.3f}",
                    f"{(df_pred['y_pred'] - df_pred['y_true']).mean():.2f} kW",
                    f"{(df_pred['y_pred'] - df_pred['y_true']).max():.2f} kW",
                    f"{(df_pred['y_pred'] - df_pred['y_true']).min():.2f} kW",
                ],
            }

            st.dataframe(pd.DataFrame(stats_data), hide_index=True, width="stretch")

    with col2:
        with st.expander("🔧 Dados da Simulação"):
            display_cols = [
                "gti",
                "air_temp",
                "cell_temp",
                "dc_power_kw",
                "dc_power_adj_kw",
                "inv_efficiency",
                "ac_power_kw_est",
            ]

            available_cols = [col for col in display_cols if col in results.columns]

            if available_cols:
                st.dataframe(results[available_cols].round(3).head(10), width="stretch")
                st.caption(f"Mostrando primeiras 10 linhas de {len(results)} registros")
            else:
                st.info("Colunas de detalhes não disponíveis")


def render_download_section(results, selected_plant_key):
    st.markdown("---")
    st.markdown("#### Download dos Resultados")

    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        csv = results.to_csv()
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M")

        st.download_button(
            label="📥 Resultados CSV",
            data=csv,
            file_name=f"simulacao_nbr_{selected_plant_key}_{timestamp}.csv",
            mime="text/csv",
            width="stretch",
        )

    with col2:
        st.button("📋 Resumo Executivo", help="Em desenvolvimento", disabled=True, width="stretch")

    with col3:
        st.markdown("**Arquivos disponíveis:**")
        st.caption("• CSV: Dados completos da simulação")
        st.caption("• Resumo: Métricas e parâmetros utilizados")


def display_simulation_results(results, df_pred, metrics, selected_plant_key):
    if results is None or df_pred is None:
        st.error("Resultados não disponíveis para exibição")
        return

    if df_pred.empty:
        st.warning("Dados de predição vazios")
        return

    if df_pred["y_true"].isnull().any():
        null_count = df_pred["y_true"].isnull().sum()
        st.warning(f"⚠️ {null_count} valores nulos encontrados nos dados reais")

    if df_pred["y_pred"].isnull().any():
        null_count = df_pred["y_pred"].isnull().sum()
        st.warning(f"⚠️ {null_count} valores nulos encontrados nos dados simulados")

    render_simulation_results(results, df_pred, metrics, selected_plant_key)
