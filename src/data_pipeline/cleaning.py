"""
cleaning.py
Kapselt die Datenbereinung(-slogik) in spezialisierten Komponenten-Klassen.
"""

import pandas as pd
from .errors import EmptyDatasetError

# ==========================================
# REINE FUNKTIONEN
# ==========================================

def filter_and_rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Reine Funktion: Filtert und benennt Spalten um."""
    relevant_features = {
        "countryName": "Country",
        "reportingYear": "Year",
        "EPRTR_SectorCode": "Code",
        "EPRTR_SectorName": "Sector",
        "facilityName": "Facility",
        "Pollutant": "Pollutant",
        "Releases": "Amount",
    }
    # Spalten filtern (und sicherstellen, dass die gefilterten Spalten existieren)
    filtered_cols = [col for col in relevant_features.keys() if col in df.columns]
    # .copy() stellt sicher, dass das Original-DataFrame nicht verändert wird
    return df[filtered_cols].rename(columns=relevant_features).copy()

def clean_numeric_values(df: pd.DataFrame) -> pd.DataFrame:
    """Reine Funktion: Konvertiert Beträge und entfernt NaN-Werte in der Zielgröße."""
    df_copy = df.copy()
    df_copy["Amount"] = pd.to_numeric(df_copy["Amount"], errors="coerce")
    return df_copy.dropna(subset=["Amount"])

def standardize_categories(df: pd.DataFrame) -> pd.DataFrame:
    """Reine Funktion: Bereinigt Textspalten von Leerzeichen und 'nan'-Strings."""
    df_copy = df.copy()
    cat_cols = ["Country", "Year", "Code", "Sector", "Facility", "Pollutant"]
    
    # Sicherstellen, dass die Spalten im DF existieren vor der Typkonvertierung
    existing_cats = [c for c in cat_cols if c in df_copy.columns]
    
    for col in existing_cats:
        df_copy[col] = df_copy[col].astype(str).str.strip()
        df_copy[col] = df_copy[col].replace({"nan": "Unknown", "": "Unknown"})
    return df_copy

# ==========================================
# OOP-KOMPONENTE
# ==========================================

class DataCleaner:
    """Komponente zur Koordinierung der Datenbereinigung und Filterung"""

    def __init__(self, df: pd.DataFrame):
        self.df_raw = df

    def clean_data(self) -> pd.DataFrame:
        """Verknüpft reine Einzelfunktionen sequentiell ohne Seiteneffekte."""
        # Schritt für Schritt durch die reinen Funktionen leiten
        df = filter_and_rename_columns(self.df_raw)
        df = clean_numeric_values(df)
        df = standardize_categories(df)

        # Geografischer Fokus auf Österreich einschränken
        if "Country" in df.columns:
            df = df[df["Country"] == "Austria"].copy()

        # Validierung mit eigener Exception
        if df.empty:
            raise EmptyDatasetError("Bereinigung fehlgeschlagen: Keine Datensätze für 'Austria' vorhanden.")
        
        return df

    def __repr__(self) -> str:
        return f"DataCleaner(RecordsIn={len(self.df_raw)})"