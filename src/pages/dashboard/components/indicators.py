def calculate_plant_health(df_stats, capacity_kwp, days_window=7):
    if df_stats.empty:
        return {"status": "sem_dados", "score": 0, "issues": ["Sem dados disponíveis"]}

    recent_data = df_stats.tail(days_window)

    avg_daily_energy = recent_data["pv_energy"].mean()
    expected_daily = capacity_kwp * 4.5
    performance_ratio = (avg_daily_energy / expected_daily) * 100 if expected_daily > 0 else 0

    cv_energy = (
        (recent_data["pv_energy"].std() / recent_data["pv_energy"].mean()) * 100
        if recent_data["pv_energy"].mean() > 0
        else 100
    )

    low_generation_days = (recent_data["pv_energy"] < (expected_daily * 0.2)).sum()

    if len(recent_data) >= 6:
        early_avg = recent_data.head(3)["pv_energy"].mean()
        late_avg = recent_data.tail(3)["pv_energy"].mean()
        trend = ((late_avg - early_avg) / early_avg) * 100 if early_avg > 0 else 0
    else:
        trend = 0

    score = 100
    issues = []

    if performance_ratio < 30:
        score -= 40
        issues.append(f"Performance muito baixa ({performance_ratio:.1f}%)")
    elif performance_ratio < 50:
        score -= 25
        issues.append(f"Performance baixa ({performance_ratio:.1f}%)")
    elif performance_ratio < 70:
        score -= 10
        issues.append(f"Performance abaixo do esperado ({performance_ratio:.1f}%)")

    if cv_energy > 80:
        score -= 20
        issues.append(f"Alta variabilidade na geração ({cv_energy:.1f}%)")
    elif cv_energy > 60:
        score -= 10
        issues.append(f"Variabilidade moderada na geração ({cv_energy:.1f}%)")

    if low_generation_days > days_window * 0.4:
        score -= 15
        issues.append(f"{low_generation_days} dias com geração muito baixa")
    elif low_generation_days > days_window * 0.2:
        score -= 8
        issues.append(f"{low_generation_days} dias com geração baixa")

    if trend < -20:
        score -= 15
        issues.append(f"Tendência de queda acentuada ({trend:.1f}%)")
    elif trend < -10:
        score -= 8
        issues.append(f"Tendência de queda ({trend:.1f}%)")

    if score >= 80:
        status = "excelente"
    elif score >= 65:
        status = "bom"
    elif score >= 45:
        status = "atencao"
    else:
        status = "critico"

    if not issues:
        issues.append("Operação normal")

    return {
        "status": status,
        "score": max(0, score),
        "performance_ratio": performance_ratio,
        "variability": cv_energy,
        "low_gen_days": low_generation_days,
        "trend": trend,
        "issues": issues,
        "avg_daily": avg_daily_energy,
        "expected_daily": expected_daily,
    }


def create_health_indicator(health_data):
    """Create visual health indicator"""
    status = health_data["status"]
    score = health_data["score"]

    colors = {"excelente": "🟢", "bom": "🟡", "atencao": "🟠", "critico": "🔴", "sem_dados": "⚫"}

    return f"{colors.get(status, '⚫')} {score:.0f}%"
