"""
train_model.py
Kapselt das unüberwachte Modell-Training des Isolation Forest und die Ergebnisse,
inkl. der ML-Artefakte für die Wiederverwendbarkeit
"""

from typing import Tuple
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# ==========================================
# REINE FUNKTIONEN
# ==========================================

def extract_ml_features(df: pd.DataFrame, feature_cols: list) -> pd.DataFrame:
    """Reine Funktion: Validiert und extrahiert die numerischen Features für den Isolation Forest."""
    missing = [col for col in feature_cols if col not in df.columns]
    if missing:
        raise KeyError(f"Fehlende Features für ML-Training: {missing}")
    return df[feature_cols].copy()

# ==========================================
# OOP-KOMPONENTE
# ==========================================

class ModelPipeline:
    """Komponente zur Vorbereitung und zum Training des Isolation Forest."""
    
    def __init__(self, df: pd.DataFrame):
        self.df_transformed = df.copy()
        self.feature_cols = [
            "Amount_Log",
            "Dev_from_Group_Median",
            "Dev_from_Sector_Median",
            "Dev_from_Sector_Group_Median",
            "YoY_Change_Pct",
        ]

    def train_pipeline(self) -> Tuple[IsolationForest, StandardScaler, pd.DataFrame, pd.DataFrame]:
        """
        Splittet die Daten, skaliert sie und trainiert den Isolation Forest.
        Gibt das trainierte Modell, den Scaler sowie Train- und Test-Feature-Sätze zurück.
        """
        # Features extrahieren über reine Funktion
        X = extract_ml_features(self.df_transformed, self.feature_cols)

        # Train-Test-Split
        X_train, X_test = train_test_split(X, test_size=0.2, random_state=42)

        # Feature-Skalierung (Wichtig für distanzbasierte/hochdimensionale Modelle)
        scaler = StandardScaler()
        X_train_normalized = scaler.fit_transform(X_train)
        X_test_normalized = scaler.transform(X_test)

        # Konvertierung zurück in DataFrames, um Spaltennamen für spätere Schritte zu erhalten
        X_train_df = pd.DataFrame(X_train_normalized, columns=self.feature_cols, index=X_train.index)
        X_test_df = pd.DataFrame(X_test_normalized, columns=self.feature_cols, index=X_test.index)

        # Modell-Fitting
        model = IsolationForest(
            n_estimators=100,
            contamination=0.05,
            random_state=42,
            n_jobs=-1
        )
        model.fit(X_train_df)
        
        return model, scaler, X_train_df, X_test_df
    
    def __repr__(self) -> str:
        return f"ModelPipeline(SelectedFeatures={len(self.feature_cols)})"