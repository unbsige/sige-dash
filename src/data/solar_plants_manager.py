import contextlib
import json
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.config.settings import BR_TZ, CREDENTIALS, DEVICE_IDS, INVERTERS_URLS


class SolarDataManager:
    def __init__(self, json_file_path="data/solar_plants.json"):
        self.json_file_path = Path(json_file_path)
        self.data = {}
        self.metadata = {}
        self.plants_data = {}
        self.campus_summary = {}
        self.environmental_impact = {}
        self.maintenance_schedule = {}
        self.system_configuration = {}

        self._df_cache = None
        self._last_modified = None
        self.load_data()

    def load_data(self):
        try:
            if not self.json_file_path.exists():
                st.error(f"Arquivo não encontrado: {self.json_file_path}")
                return

            current_modified = self.json_file_path.stat().st_mtime
            if self._last_modified != current_modified:
                self._last_modified = current_modified
                self._df_cache = None

                with open(self.json_file_path, encoding="utf-8") as f:
                    self.data = json.load(f)

                self.metadata = self.data.get("metadata", {})
                self.plants_data = self.data.get("plants", {})
                self.campus_summary = self.data.get("campus_summary", {})
                self.environmental_impact = self.data.get("environmental_impact", {})
                self.maintenance_schedule = self.data.get("maintenance_schedule", {})
                self.system_configuration = self.data.get("system_configuration", {})

        except Exception as e:
            st.error(f"Erro ao carregar dados: {str(e)}")

    def load_env_data(self, plant):
        code = plant.get("code", None)

        if not code:
            st.error("Código da planta não encontrado.")
            return plant

        if code not in CREDENTIALS:
            st.error(f"Credenciais não encontradas para a planta: {code}")

        if code not in DEVICE_IDS:
            st.error(f"ID do dispositivo não encontrado para a planta: {code}")

        plant["credentials"] = CREDENTIALS.get(code)
        plant["device"] = DEVICE_IDS.get(code)
        return plant

    def get_dataframe(self) -> pd.DataFrame:
        if self._df_cache is not None:
            return self._df_cache

        if not self.plants_data:
            return pd.DataFrame()

        rows = []
        for code, plant in self.plants_data.items():
            row = {
                "Código": code,
                "Nome": plant.get("acronym", code.upper()),
                "Edifício": plant.get("building", ""),
                "Campus": plant.get("campus", ""),
                "Status": plant.get("status", "Ativa"),
                "Potência (kWp)": float(plant.get("power_kwp", 0)),
                "Geração Anual (kWh)": float(plant.get("annual_generation_kwh", 0)),
                "Latitude": float(plant.get("coordinates", {}).get("latitude", 0)),
                "Longitude": float(plant.get("coordinates", {}).get("longitude", 0)),
                "Data Instalação": plant.get("installation_date", ""),
                "Tem Device ID": bool(plant.get("device", {}).get("device_id", "")),
                "Fabricante": plant.get("device", {}).get("manufacturer", ""),
                "Modelo Device": plant.get("device", {}).get("model", ""),
                "Qtd Painéis": int(plant.get("technical_specs", {}).get("panel_count", 0)),
                "Potência Painel (Wp)": int(plant.get("technical_specs", {}).get("panel_power_wp", 0)),
                "Qtd Strings": int(plant.get("technical_specs", {}).get("string_count", 0)),
                "Modelo Inversor": plant.get("technical_specs", {}).get("inverter_model", ""),
            }
            rows.append(row)

        self._df_cache = pd.DataFrame(rows)
        return self._df_cache

    def get_summary_metrics(self):
        """Retorna métricas de resumo usando dados dos metadados quando disponível"""
        if self.metadata:
            return {
                "total_plants": self.metadata.get("total_plants", len(self.plants_data)),
                "total_power_kwp": self.metadata.get("total_power_kwp", 0),
                "total_generation_kwh": self.metadata.get("total_annual_generation_kwh", 0),
                "active_plants": len([p for p in self.plants_data.values() if p.get("status") == "Ativa"]),
                "campus_count": self.metadata.get("campus_count", 0),
                "avg_power_per_plant": self.metadata.get("total_power_kwp", 0)
                / max(self.metadata.get("total_plants", 1), 1),
                "environmental_impact": self.environmental_impact,
                "campus_breakdown": self.campus_summary,
                "university": self.metadata.get("university", ""),
                "last_updated": self.metadata.get("last_updated", ""),
            }

        if not self.plants_data:
            return {}

        df = self.get_dataframe()
        return {
            "total_plants": len(self.plants_data),
            "total_power_kwp": df["Potência (kWp)"].sum(),
            "total_generation_kwh": df["Geração Anual (kWh)"].sum(),
            "active_plants": len(df[df["Status"] == "Ativa"]),
            "campus_count": len(df["Campus"].unique()),
            "avg_power_per_plant": df["Potência (kWp)"].mean(),
            "largest_plant": df.loc[df["Potência (kWp)"].idxmax()].to_dict() if len(df) > 0 else {},
            "smallest_plant": df.loc[df["Potência (kWp)"].idxmin()].to_dict() if len(df) > 0 else {},
            "total_panels": df["Qtd Painéis"].sum(),
            "environmental_impact": self.environmental_impact,
        }

    def get_plant_by_code(self, code):
        return self.plants_data.get(code)

    def get_plants_by_campus(self, campus):
        """Busca plantas por campus (case-insensitive)"""
        return {
            code: plant
            for code, plant in self.plants_data.items()
            if plant.get("campus", "").lower() == campus.lower()
        }

    def get_plants_by_status(self, status):
        return {
            code: plant
            for code, plant in self.plants_data.items()
            if plant.get("status", "").lower() == status.lower()
        }

    def search_plants(self, keyword):
        keyword = keyword.lower()
        results = {}

        for code, plant in self.plants_data.items():
            searchable_text = " ".join([
                code.lower(),
                plant.get("acronym", "").lower(),
                plant.get("building", "").lower(),
                plant.get("campus", "").lower(),
            ])

            if keyword in searchable_text:
                results[code] = plant

        return results

    def get_plants_without_credentials(self):
        return {
            code: plant
            for code, plant in self.plants_data.items()
            if not plant.get("credentials", {}).get("username", "").strip()
        }

    def get_plants_without_device_id(self):
        return {
            code: plant
            for code, plant in self.plants_data.items()
            if not plant.get("device", {}).get("device_id", "").strip()
        }

    def get_recent_installations(self, days=365):
        cutoff_date = datetime.now() - timedelta(days=days)
        results = {}

        for code, plant in self.plants_data.items():
            install_date_str = plant.get("installation_date", "")
            if install_date_str:
                with contextlib.suppress(Exception):
                    try:
                        install_date = datetime.fromisoformat(install_date_str)
                    except:
                        install_date = datetime.strptime(install_date_str, "%Y-%m-%d")

                    if install_date >= cutoff_date:
                        results[code] = plant
        return results

    def get_selectbox_options(self, status=None):
        if not self.plants_data:
            return {}

        df = self.get_dataframe()

        if status is not None:
            df = df[df["Status"] == status]

        years = []
        for date in df["Data Instalação"].dropna():
            if isinstance(date, str) and len(date) >= 4:
                try:
                    years.append(date[:4])
                except Exception:
                    continue

        plants_dict = {}
        for code, plant in self.plants_data.items():
            if status is None or plant.get("status") == status:
                key = f"{plant.get('acronym', code)} ({plant.get('building', code)})"
                plants_dict[key] = plant

        return {
            "plants": plants_dict,
            "campus": sorted([c for c in df["Campus"].unique() if c]),
            "status": sorted([s for s in df["Status"].unique() if s]),
            "manufacturers": sorted([m for m in df["Fabricante"].dropna().unique() if m]),
            "years": sorted(list(set(years))),
        }

    def get_plant_from_selectbox(self, selection):
        if not selection or "(" not in selection:
            return None

        code = selection.split("(")[-1].replace(")", "")
        return self.get_plant_by_code(code)

    def apply_filters(self, filters: dict) -> pd.DataFrame:
        df = self.get_dataframe()

        for column, values in filters.items():
            if values and column in df.columns and len(values) > 0:
                df = df[df[column].isin(values)]

        return df

    def create_power_by_campus_chart(self):
        """Criar gráfico usando dados do campus_summary se disponível"""
        if self.campus_summary:
            campus_data = []
            for campus, data in self.campus_summary.items():
                campus_data.append({
                    "Campus": campus,
                    "Potência (kWp)": data.get("total_power_kwp", 0),
                    "Usinas": data.get("plant_count", 0),
                })
            campus_df = pd.DataFrame(campus_data)
        else:
            # Fallback para cálculo manual
            df = self.get_dataframe()
            campus_df = df.groupby("Campus").agg({"Potência (kWp)": "sum", "Código": "count"}).reset_index()
            campus_df.rename(columns={"Código": "Usinas"}, inplace=True)

        fig = px.bar(
            campus_df,
            x="Campus",
            y="Potência (kWp)",
            title="Potência Instalada por Campus",
            color="Campus",
            text="Potência (kWp)",
            hover_data=["Usinas"],
        )
        fig.update_traces(texttemplate="%{text:.1f} kWp", textposition="outside")
        fig.update_layout(showlegend=False)
        return fig

    def create_power_vs_generation_chart(self):
        df = self.get_dataframe()

        return px.scatter(
            df,
            x="Potência (kWp)",
            y="Geração Anual (kWh)",
            color="Campus",
            size="Potência (kWp)",
            hover_data=["Nome", "Edifício"],
            title="Potência vs Geração Anual",
        )

    def create_map_chart(self):
        df = self.get_dataframe()
        df_with_coords = df[(df["Latitude"] != 0) & (df["Longitude"] != 0)]

        if len(df_with_coords) == 0:
            return None

        fig = px.scatter_mapbox(
            df_with_coords,
            lat="Latitude",
            lon="Longitude",
            hover_name="Nome",
            hover_data=["Campus", "Potência (kWp)", "Status"],
            color="Campus",
            size="Potência (kWp)",
            zoom=10,
            height=500,
            title="Localização das Usinas Fotovoltaicas",
        )
        fig.update_layout(mapbox_style="open-street-map")
        return fig

    def get_campus_analysis(self):
        """Retorna análise usando campus_summary se disponível"""
        if self.campus_summary:
            analysis = {}
            df = self.get_dataframe()

            for campus, summary in self.campus_summary.items():
                campus_df = df[df["Campus"] == campus]

                analysis[campus] = {
                    "plant_count": summary.get("plant_count", 0),
                    "total_power": summary.get("total_power_kwp", 0),
                    "total_generation": summary.get("total_generation_kwh", 0),
                    "percentage_of_total": summary.get("percentage_of_total", 0),
                    "avg_power_per_plant": summary.get("total_power_kwp", 0) / max(summary.get("plant_count", 1), 1),
                    "largest_plant": campus_df.loc[campus_df["Potência (kWp)"].idxmax()]["Nome"]
                    if len(campus_df) > 0
                    else "N/A",
                    "total_panels": campus_df["Qtd Painéis"].sum(),
                    "configuration_status": {
                        "with_device_id": len(campus_df[campus_df["Tem Device ID"] == True]),
                        "without_device_id": len(campus_df[campus_df["Tem Device ID"] == False]),
                    },
                }
            return analysis

        # Fallback para cálculo manual
        df = self.get_dataframe()
        analysis = {}

        for campus in df["Campus"].unique():
            if not campus:
                continue

            campus_df = df[df["Campus"] == campus]

            analysis[campus] = {
                "plant_count": len(campus_df),
                "total_power": campus_df["Potência (kWp)"].sum(),
                "total_generation": campus_df["Geração Anual (kWh)"].sum(),
                "avg_power_per_plant": campus_df["Potência (kWp)"].mean(),
                "largest_plant": campus_df.loc[campus_df["Potência (kWp)"].idxmax()]["Nome"]
                if len(campus_df) > 0
                else "N/A",
                "total_panels": campus_df["Qtd Painéis"].sum(),
                "configuration_status": {
                    "with_device_id": len(campus_df[campus_df["Tem Device ID"] == True]),
                    "without_device_id": len(campus_df[campus_df["Tem Device ID"] == False]),
                },
            }

        return analysis

    def export_filtered_data(self, filters: dict, format="csv") -> str:
        df = self.apply_filters(filters)

        if format.lower() == "csv":
            return df.to_csv(index=False)
        elif format.lower() == "json":
            return df.to_json(orient="records", ensure_ascii=False, indent=2)
        else:
            return ""

    def save_updated_data(self):
        df = self.get_dataframe()

        self.data["metadata"]["last_updated"] = datetime.now().isoformat()
        self.data["metadata"]["total_plants"] = len(self.plants_data)
        self.data["metadata"]["total_power_kwp"] = df["Potência (kWp)"].sum()
        self.data["metadata"]["total_annual_generation_kwh"] = df["Geração Anual (kWh)"].sum()
        self.data["metadata"]["campus_count"] = len(df["Campus"].unique())

        self.data["plants"] = self.plants_data

        with open(self.json_file_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

        self._df_cache = None
        self._last_modified = None

    def update_plant_credentials(self, code, username, password) -> bool:
        if code in self.plants_data:
            if "credentials" not in self.plants_data[code]:
                self.plants_data[code]["credentials"] = {}
            self.plants_data[code]["credentials"]["username"] = username
            self.plants_data[code]["credentials"]["password"] = password
            self.save_updated_data()
            return True
        return False

    def update_plant_device(self, code, model, device_id, manufacturer="") -> bool:
        if code in self.plants_data:
            if "device" not in self.plants_data[code]:
                self.plants_data[code]["device"] = {}
            self.plants_data[code]["device"]["model"] = model
            self.plants_data[code]["device"]["device_id"] = device_id
            if manufacturer:
                self.plants_data[code]["device"]["manufacturer"] = manufacturer
            self.save_updated_data()
            return True
        return False

    def reload_data(self):
        """Força recarregamento completo dos dados"""
        self._last_modified = None
        self._df_cache = None
        if hasattr(st, "cache_data"):
            st.cache_data.clear()
        self.load_data()

    def validate_data_integrity(self):
        issues = []

        if not self.plants_data:
            issues.append("Nenhuma planta carregada")
            return issues

        for code, plant in self.plants_data.items():
            required_fields = ["power_kwp", "annual_generation_kwh", "status", "campus"]
            for field in required_fields:
                if field not in plant or plant[field] is None:
                    issues.append(f"Planta {code}: campo obrigatório '{field}' ausente")

            coords = plant.get("coordinates", {})
            if not coords.get("latitude") or not coords.get("longitude"):
                issues.append(f"Planta {code}: coordenadas inválidas ou ausentes")

            tech_specs = plant.get("technical_specs", {})
            if not tech_specs.get("panel_count"):
                issues.append(f"Planta {code}: número de painéis não informado")

        return issues
