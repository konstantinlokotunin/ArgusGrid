"""
evaluate_model.py
Berechnet rein mathematische Auswertungen und aggregiert Ergebnisse.
"""

import pandas as pd

# ==========================================
# REINE FUNKTIONEN
# ==========================================

def calculate_anomaly_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Reine Funktion: Berechnet die globalen Anomalie-Kennzahlen."""
    total_samples = len(df)
    anomaly_count = int(df["Is_Anomaly"].sum())
    anomaly_rate = round(anomaly_count / total_samples * 100, 2) if total_samples > 0 else 0.0

    return pd.DataFrame({
        "Total samples": [total_samples],
        "Detected anomalies": [anomaly_count],
        "Anomaly Rate %": [anomaly_rate]
    })

def aggregate_by_column(df: pd.DataFrame, column_name: str | list) -> pd.DataFrame:
    """Reine Funktion: Aggregiert Anomalien nach einer bestimmten Kategorie (Sektor/Gruppe)."""
    return (
        df[df["Is_Anomaly"] == 1]
        .groupby(column_name)
        .size()
        .sort_values(ascending=False)
        .reset_index(name="Anomalien_Anzahl")
    )

# ==========================================
# OOP-KOMPONENTE
# ==========================================

class ReportGenerator:
    """Komponente zur Strukturierung der Reports."""
    
    def __init__(self, df: pd.DataFrame):
        self.df_results = df

    def build_reports(self) -> dict:
        """Sammelt alle berechneten Reports in einem Dictionary."""
        return {
            "Summary": calculate_anomaly_summary(self.df_results),
            "Top_20_Anomalien": self.df_results.sort_values("Anomaly_Score", ascending=True).head(20),
            "Nach_Sektor": aggregate_by_column(self.df_results, "Sector"),
            "Nach_Stoffgruppe": aggregate_by_column(self.df_results, "Pollutant_Group"),
            "Nach_Sektor_und_Stoffgruppe": aggregate_by_column(self.df_results, ["Sector", "Pollutant_Group"])
        }

    def __repr__(self) -> str:
        return f"ReportGenerator(Rows={len(self.df_results)})"