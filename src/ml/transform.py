"""
transform.py
Kapselt die Schadstoff-Klassifizierung und Feature-Engineering-Logik.
"""

import pandas as pd
import numpy as np

# Globales, statisches Dictionary für das Mapping (sauber und übersichtlich)
RISK_GROUPS = {
    "Critical Risk": [
        "Arsenic and compounds (as As)", "Asbestos", "Benzene", "Cadmium and compounds (as Cd)",
        "Chlordecone", "Chromium and compounds (as Cr)", "Endrin", "Ethylene oxide",
        "Hydrogen cyanide (HCN)", "Lead and compounds (as Pb)", "Mercury and compounds (as Hg)",
        "PCDD + PCDF (dioxins + furans) (as Teq)", "Vinyl chloride"
    ],
    "High Risk": [
        "1,1,1-trichloroethane (TCE-1,1,1)", "1,1,2,2-tetrachloroethane (TETRACHLOROETHANE-1,1,2,2)",
        "1,2,3,4,5,6-hexachlorocyclohexane (HCH)", "1,2-dichloroethane (DCE-1,2)", "Aldrin",
        "Anthracene", "Benzo(g,h,i)perylene", "Brominated diphenylethers (PBDE)",
        "Di-(2-ethyl hexyl) phthalate (DEHP)", "Dichloromethane (DCM)", "Fluoranthene",
        "Halogenated organic compounds (as AOX)", "Hexachlorobenzene (HCB)", "Lindane",
        "Naphthalene", "Nickel and compounds (as Ni)", "Nonylphenol and Nonylphenol ethoxylates",
        "Pentachlorobenzene", "Pentachlorophenol (PCP)", "Polychlorinated biphenyls (PCBs)",
        "Polycyclic aromatic hydrocarbons (PAHs)", "Tetrachloroethylene", "Tetrachloromethane (TCM)",
        "Trichlorobenzenes (TCB)", "Trichloroethylene (TRI)", "Trichloromethane"
    ],
    "Moderate Risk": [
        "Ammonia (NH3)", "Carbon monoxide (CO)", "Chlorine and inorganic compounds (as HCl)",
        "Copper and compounds (as Cu)", "Fine particulate matter (PM2.5)", "Fluorides (as total F)",
        "Fluorine and inorganic compounds (as HF)", "Nitrogen oxides (NOX)",
        "Non-methane volatile organic compounds (NMVOC)", "Particulate matter (PM10)",
        "Phenols (as total C)", "Sulphur oxides (SOX)", "Zinc and compounds (as Zn)"
    ],
    "Regulated Climate/Ozone Risk": [
        "Carbon dioxide (CO2)", "Carbon dioxide (CO2) excluding biomass", "Chlorofluorocarbons (CFCs)",
        "Halons", "Hydro-fluorocarbons (HFCS)", "Hydrochlorofluorocarbons (HCFCs)",
        "Methane (CH4)", "Nitrous oxide (N2O)", "Perfluorocarbons (PFCs)", "Sulphur hexafluoride (SF6)"
    ],
    "Low / Context-dependent Risk": [
        "Chlorides (as total Cl)", "Ethyl benzene", "Toluene", "Total nitrogen",
        "Total organic carbon(as total C or COD/3) (TOC)", "Xylenes"
    ]
}

# # Flacher Lookup-Index für O(1) Performance
risk_lookup = {
    substance: risk_level
    for risk_level, substances in RISK_GROUPS.items()
    for substance in substances
    }
        
# ==========================================
# REINE FUNKTIONEN
# ==========================================

def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Reine Funktion: Berechnet Basis-Features, Log-Transformation,
    Abweichungen von den Gruppen- und Sektor-Medianen sowie
    Year-over-Year (YoY) Änderungen ohne mathematische Fehler.
    """
    df_copy = df.copy()
    
    # Vektorisierte Zuordnung der Luftschadstoffgruppe
    df_copy["Pollutant_Group"] = df_copy["Pollutant"].map(risk_lookup).fillna("Unclassified")
    
    # Flags für unplausible/negative Werte setzen & Logarithmus absichern
    df_copy["Is_Negative"] = df_copy["Amount"] < 0
    safe_amount = df_copy["Amount"].clip(lower=0)
    df_copy["Amount_Log"] = np.log1p(safe_amount)
    
    # Abweichung Sektoren-Median
    df_copy["Sector_Median"] = df_copy.groupby("Sector")["Amount_Log"].transform("median")
    df_copy["Dev_from_Sector_Median"] = df_copy["Amount_Log"] - df_copy["Sector_Median"]

    # Abweichung Gruppen-Median
    df_copy["Group_Median"] = df_copy.groupby("Pollutant_Group")["Amount_Log"].transform("median")
    df_copy["Dev_from_Group_Median"] = df_copy["Amount_Log"] - df_copy["Group_Median"]
    
    # Kombinierter Median
    df_copy["Sector_Group_Median"] = df_copy.groupby(["Sector", "Pollutant_Group"])["Amount_Log"].transform("median")
    df_copy["Dev_from_Sector_Group_Median"] = df_copy["Amount_Log"] - df_copy["Sector_Group_Median"]

    # Year-over-Year (YoY) Prozentsatz und Änderungen zeitlich korrekt berechnen
    df_copy = df_copy.sort_values(["Facility", "Pollutant", "Year"])
    df_copy["Previous_Year_Amount"] = df_copy.groupby(["Facility", "Pollutant"])["Amount"].shift(1)
    df_copy["YoY_Change_Pct"] = ((df_copy["Amount"] - df_copy["Previous_Year_Amount"]) / df_copy["Previous_Year_Amount"]) * 100
    # Guardrails: Unendliche Werte abfangen
    df_copy["YoY_Change_Pct"] = df_copy["YoY_Change_Pct"].replace([np.inf, -np.inf], np.nan).fillna(0.0)

    return df_copy

# ==========================================
# OOP-KOMPONENTE
# ==========================================

class DataTransformer:
    """Komponente zur hochdimensionalen Feature-Generierung."""
    
    def __init__(self, df: pd.DataFrame):
        self.df_cleaned = df

    def transform_data(self) -> pd.DataFrame:
        """Verknüpft reine Einzelfunktionen sequentiell ohne Seiteneffekte."""
        # Schritt für Schritt durch die reinen Funktionen leiten
        df = add_features(self.df_cleaned)
    
        return df

    def __repr__(self) -> str:
        return f"DataTransformer(ColumnsIn={len(self.df_cleaned.columns)})"