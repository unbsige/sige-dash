"""
Dashboard de Sustentabilidade - Usinas Fotovoltaicas Campus Darcy Ribeiro
Configurações para relatórios e monitoramento em tempo real
Data: 2025
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any

# --------------------------------------------------------------------------------------
# CONFIGURAÇÕES DO DASHBOARD
# --------------------------------------------------------------------------------------

DASHBOARD_CONFIG = {
    "title": "Dashboard de Sustentabilidade - Campus Darcy Ribeiro",
    "subtitle": "Monitoramento de Energia Solar Fotovoltaica",
    "refresh_interval_seconds": 300,  # 5 minutos
    "timezone": "America/Sao_Paulo",
    "currency": "BRL"
}

# --------------------------------------------------------------------------------------
# MÉTRICAS PRINCIPAIS PARA O DASHBOARD GERAL
# --------------------------------------------------------------------------------------

GENERAL_METRICS = {
    # Visão Geral Instantânea
    "overview": {
        "current_total_generation_kw": "Geração Atual Total",
        "today_generation_kwh": "Geração Hoje",
        "month_generation_kwh": "Geração do Mês",
        "year_generation_kwh": "Geração do Ano",
        "total_installed_power_kwp": "Potência Total Instalada",
        "active_plants_count": "Usinas Ativas",
        "system_availability_percent": "Disponibilidade do Sistema"
    },
    
    # Indicadores de Performance
    "performance": {
        "capacity_factor_today": "Fator de Capacidade Hoje (%)",
        "capacity_factor_month": "Fator de Capacidade do Mês (%)",
        "performance_ratio_today": "Taxa de Performance Hoje (%)",
        "peak_power_today_kw": "Pico de Potência Hoje",
        "peak_power_time": "Horário do Pico",
        "generation_vs_forecast_percent": "Geração vs Previsão (%)"
    },
    
    # Impacto Ambiental
    "environmental": {
        "co2_avoided_today_kg": "CO₂ Evitado Hoje (kg)",
        "co2_avoided_month_kg": "CO₂ Evitado no Mês (kg)",
        "co2_avoided_year_tons": "CO₂ Evitado no Ano (t)",
        "trees_equivalent": "Árvores Equivalentes",
        "coal_avoided_kg": "Carvão Evitado (kg)",
        "water_saved_liters": "Água Economizada (L)"
    },
    
    # Impacto Econômico
    "economic": {
        "savings_today_brl": "Economia Hoje (R$)",
        "savings_month_brl": "Economia do Mês (R$)",
        "savings_year_brl": "Economia do Ano (R$)",
        "accumulated_savings_brl": "Economia Acumulada (R$)",
        "roi_percent": "Retorno sobre Investimento (%)",
        "payback_years": "Payback (anos)"
    }
}

# --------------------------------------------------------------------------------------
# MÉTRICAS POR PLANTA INDIVIDUAL
# --------------------------------------------------------------------------------------

PLANT_METRICS = {
    "status": {
        "plant_code": "Código da Usina",
        "plant_name": "Nome da Usina",
        "current_power_kw": "Potência Atual (kW)",
        "installed_power_kwp": "Potência Instalada (kWp)",
        "status": "Status (Online/Offline/Manutenção)",
        "last_update": "Última Atualização",
        "uptime_percent": "Tempo Online (%)"
    },
    "generation": {
        "generation_5min_kwh": "Geração Últimos 5min",
        "generation_today_kwh": "Geração Hoje",
        "generation_week_kwh": "Geração da Semana",
        "generation_month_kwh": "Geração do Mês",
        "generation_year_kwh": "Geração do Ano",
        "generation_total_mwh": "Geração Total Histórica"
    },
    "performance": {
        "efficiency_percent": "Eficiência (%)",
        "capacity_factor": "Fator de Capacidade",
        "performance_ratio": "Taxa de Performance",
        "specific_yield_kwh_kwp": "Rendimento Específico",
        "peak_power_today": "Pico Hoje",
        "avg_daily_generation": "Média Diária"
    },
    "comparatives": {
        "vs_yesterday_percent": "vs Ontem (%)",
        "vs_last_month_percent": "vs Mês Passado (%)",
        "vs_forecast_percent": "vs Previsão (%)",
        "vs_campus_average_percent": "vs Média do Campus (%)",
        "ranking_position": "Posição no Ranking"
    }
}

# --------------------------------------------------------------------------------------
# PERÍODOS DE ANÁLISE
# --------------------------------------------------------------------------------------

TIME_PERIODS = {
    "real_time": {
        "interval": "5min",
        "description": "Tempo Real",
        "retention_days": 7
    },
    "hourly": {
        "interval": "1h",
        "description": "Por Hora",
        "retention_days": 30
    },
    "daily": {
        "interval": "1d",
        "description": "Diário",
        "retention_days": 365
    },
    "weekly": {
        "interval": "7d",
        "description": "Semanal",
        "retention_weeks": 52
    },
    "monthly": {
        "interval": "1M",
        "description": "Mensal",
        "retention_months": 60
    },
    "yearly": {
        "interval": "1Y",
        "description": "Anual",
        "retention_years": 25
    }
}

# --------------------------------------------------------------------------------------
# ALERTAS E NOTIFICAÇÕES
# --------------------------------------------------------------------------------------

ALERT_THRESHOLDS = {
    "performance": {
        "low_generation_percent": 70,  # Geração abaixo de 70% do esperado
        "system_offline_minutes": 15,  # Sistema offline por mais de 15min
        "low_efficiency_percent": 80,  # Eficiência abaixo de 80%
        "high_temperature_celsius": 75  # Temperatura alta nos equipamentos
    },
    "maintenance": {
        "cleaning_needed_days": 30,  # Limpeza necessária a cada 30 dias
        "inspection_needed_months": 6,  # Inspeção a cada 6 meses
        "inverter_efficiency_min": 95  # Eficiência mínima do inversor
    },
    "economic": {
        "savings_target_percent": 85,  # Meta de economia atingida
        "cost_threshold_brl": 1000  # Custo de manutenção acima do limite
    }
}

# --------------------------------------------------------------------------------------
# CONFIGURAÇÕES DE RELATÓRIOS
# --------------------------------------------------------------------------------------

REPORT_TEMPLATES = {
    "executive_monthly": {
        "frequency": "monthly",
        "format": "pdf",
        "sections": [
            "resumo_executivo",
            "performance_campus",
            "impacto_ambiental",
            "economia_financeira",
            "comparativo_historico",
            "recomendacoes"
        ]
    },
    "technical_weekly": {
        "frequency": "weekly",
        "format": "excel",
        "sections": [
            "dados_operacionais",
            "performance_plantas",
            "alertas_manutencao",
            "analise_tendencias",
            "graficos_detalhados"
        ]
    },
    "sustainability_annual": {
        "frequency": "yearly",
        "format": "pdf",
        "sections": [
            "impacto_ambiental_anual",
            "metas_sustentabilidade",
            "comparativo_anos_anteriores",
            "projecoes_futuras",
            "certificacoes"
        ]
    },
    "operational_daily": {
        "frequency": "daily",
        "format": "email",
        "sections": [
            "resumo_dia",
            "alertas_ativos",
            "performance_plantas",
            "previsao_proximo_dia"
        ]
    }
}

# --------------------------------------------------------------------------------------
# KPIS PRINCIPAIS
# --------------------------------------------------------------------------------------

KEY_PERFORMANCE_INDICATORS = {
    # KPIs Operacionais
    "operational": {
        "availability": {
            "name": "Disponibilidade do Sistema",
            "target": 98.5,
            "unit": "%",
            "calculation": "tempo_online / tempo_total * 100"
        },
        "capacity_factor": {
            "name": "Fator de Capacidade",
            "target": 16.0,
            "unit": "%",
            "calculation": "energia_gerada / (potencia_instalada * horas_periodo) * 100"
        },
        "performance_ratio": {
            "name": "Taxa de Performance",
            "target": 85.0,
            "unit": "%",
            "calculation": "energia_real / energia_teorica * 100"
        }
    },
    
    # KPIs Ambientais
    "environmental": {
        "co2_intensity": {
            "name": "Intensidade de CO₂ Evitado",
            "target": 0.5,
            "unit": "kg CO₂/kWh",
            "calculation": "co2_evitado / energia_gerada"
        },
        "renewable_percentage": {
            "name": "Percentual de Energia Renovável",
            "target": 100.0,
            "unit": "%",
            "calculation": "energia_solar / energia_total_campus * 100"
        }
    },
    
    # KPIs Econômicos
    "economic": {
        "cost_per_kwh": {
            "name": "Custo por kWh Gerado",
            "target": 0.12,
            "unit": "R$/kWh",
            "calculation": "custo_total / energia_gerada"
        },
        "savings_rate": {
            "name": "Taxa de Economia",
            "target": 25.0,
            "unit": "%",
            "calculation": "economia_energia / custo_energia_convencional * 100"
        }
    }
}

# --------------------------------------------------------------------------------------
# CONFIGURAÇÕES DE VISUALIZAÇÃO
# --------------------------------------------------------------------------------------

VISUALIZATION_CONFIG = {
    "colors": {
        "primary": "#2E8B57",  # Verde para energia limpa
        "secondary": "#FFA500",  # Laranja para alertas
        "success": "#32CD32",  # Verde claro para metas atingidas
        "warning": "#FFD700",  # Amarelo para atenção
        "danger": "#FF6347",  # Vermelho para alertas críticos
        "info": "#4682B4"  # Azul para informações
    },
    
    "chart_types": {
        "generation_timeline": "line_chart",
        "plant_comparison": "bar_chart",
        "environmental_impact": "donut_chart",
        "efficiency_heatmap": "heatmap",
        "forecast_vs_actual": "dual_line_chart"
    },
    
    # Configurações de Mapa
    "map_config": {
        "center_coordinates": (-15.763564, -47.872538),
        "zoom_level": 16,
        "plant_marker_size": "power_proportional",
        "show_generation_animation": True
    }
}

# --------------------------------------------------------------------------------------
# INTEGRAÇÃO COM SISTEMAS EXTERNOS
# --------------------------------------------------------------------------------------

INTEGRATION_CONFIG = {
    # APIs Meteorológicas
    "weather_api": {
        "provider": "OpenWeather",
        "update_interval_minutes": 30,
        "parameters": ["irradiance", "temperature", "humidity", "cloud_cover"]
    },
    
    # Sistema de Faturamento UnB
    "billing_system": {
        "sync_frequency": "daily",
        "energy_tariff_source": "ANEEL",
        "currency_conversion": True
    },
    
    # Sistema de Monitoramento de Equipamentos
    "equipment_monitoring": {
        "inverter_data": True,
        "string_monitoring": True,
        "environmental_sensors": True
    }
}

# --------------------------------------------------------------------------------------
# FUNÇÕES AUXILIARES PARA DASHBOARD
# --------------------------------------------------------------------------------------

def get_dashboard_metrics() -> Dict[str, Any]:
    """Retorna estrutura completa de métricas para o dashboard"""
    return {
        "general": GENERAL_METRICS,
        "plant_specific": PLANT_METRICS,
        "time_periods": TIME_PERIODS,
        "kpis": KEY_PERFORMANCE_INDICATORS
    }

def get_alert_config() -> Dict[str, Any]:
    """Retorna configurações de alertas"""
    return ALERT_THRESHOLDS

def get_report_templates() -> Dict[str, Any]:
    """Retorna templates de relatórios disponíveis"""
    return REPORT_TEMPLATES

def calculate_environmental_metrics(generation_kwh: float) -> Dict[str, float]:
    """Calcula métricas ambientais baseadas na geração"""
    co2_factor = 0.0817  # kg CO2/kWh
    trees_per_ton_co2 = 40
    water_factor = 2.5  # L/kWh
    coal_factor = 0.4  # kg/kWh
    
    co2_avoided_kg = generation_kwh * co2_factor
    trees_equivalent = (co2_avoided_kg / 1000) * trees_per_ton_co2
    water_saved_l = generation_kwh * water_factor
    coal_avoided_kg = generation_kwh * coal_factor
    
    return {
        "co2_avoided_kg": co2_avoided_kg,
        "co2_avoided_tons": co2_avoided_kg / 1000,
        "trees_equivalent": trees_equivalent,
        "water_saved_liters": water_saved_l,
        "coal_avoided_kg": coal_avoided_kg
    }

def get_dashboard_layout() -> List[Dict[str, Any]]:
    """Define layout do dashboard"""
    return [
        {
            "section": "header",
            "components": ["total_generation", "current_power", "system_status", "weather"]
        },
        {
            "section": "kpi_cards",
            "components": ["today_generation", "month_generation", "co2_savings", "financial_savings"]
        },
        {
            "section": "main_charts",
            "components": ["generation_timeline", "plant_comparison", "efficiency_trend"]
        },
        {
            "section": "plant_grid",
            "components": ["individual_plant_cards"]
        },
        {
            "section": "environmental",
            "components": ["environmental_impact_chart", "sustainability_metrics"]
        },
        {
            "section": "alerts",
            "components": ["active_alerts", "maintenance_schedule"]
        }
    ]

# --------------------------------------------------------------------------------------
# EXEMPLO DE USO
# --------------------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== CONFIGURAÇÃO DO DASHBOARD DE SUSTENTABILIDADE ===")
    print(f"Título: {DASHBOARD_CONFIG['title']}")
    print(f"Atualização: a cada {DASHBOARD_CONFIG['refresh_interval_seconds']} segundos")
    
    # Exemplo de cálculo de métricas ambientais
    exemplo_geracao = 10000  # kWh
    metricas_amb = calculate_environmental_metrics(exemplo_geracao)
    
    print(f"\nExemplo - Geração de {exemplo_geracao:,} kWh:")
    print(f"- CO₂ evitado: {metricas_amb['co2_avoided_kg']:.1f} kg")
    print(f"- Árvores equivalentes: {metricas_amb['trees_equivalent']:.0f}")
    print(f"- Água economizada: {metricas_amb['water_saved_liters']:,.0f} litros")
    
    print(f"\nKPIs Principais:")
    for categoria, kpis in KEY_PERFORMANCE_INDICATORS.items():
        print(f"\n{categoria.upper()}:")
        for kpi, config in kpis.items():
            print(f"  - {config['name']}: Meta {config['target']}{config['unit']}")