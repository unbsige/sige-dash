from plotly import graph_objects as go


def get_status_emoji(status):
    if status == "online":
        return "✅"
    elif status == "warning":
        return "⚠️"
    else:
        return "❌"


def get_status_emoji_basic(status):
    if status == "online":
        return "🟢"
    elif status == "warning":
        return "🟡"
    else:
        return "🔴"


def get_status_color(status):
    if status == "online":
        return "#10b981"
    elif status == "warning":
        return "#f59e0b"
    else:
        return "#ef4444"


def get_status_text(status):
    if status == "online":
        return "Online"
    elif status == "warning":
        return "Atenção"
    else:
        return "Offline"


def create_mini_chart(dados_hora):
    try:
        if not dados_hora or not isinstance(dados_hora, list | tuple):
            dados_hora = [0, 0, 0, 0, 0, 0, 0]

        horas = ["6h", "8h", "10h", "12h", "14h", "16h", "18h"]

        if len(dados_hora) != len(horas):
            dados_hora = dados_hora[: len(horas)] + [0] * max(0, len(horas) - len(dados_hora))

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=horas,
                y=dados_hora,
                mode="lines",
                line=dict(color="#3b82f6", width=2),
                fill="tonexty",
                fillcolor="rgba(59, 130, 246, 0.1)",
                showlegend=False,
                hovertemplate="%{x}: %{y:.0f} kW<extra></extra>",
            )
        )

        fig.update_layout(
            height=60,
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        )

        return fig

    except Exception:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=[0], y=[0], mode="markers", marker=dict(size=0)))
        fig.update_layout(
            height=60,
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        )
        return fig


# --------------------------------------------------------------------------------------------------------------------

#             co2_avoided = total_energy * 0.46
#             if co2_avoided >= 1000:
#                 st.caption(f"🌱 Evita ~{co2_avoided / 1000:.1f}t CO₂")
#             else:
#
