"""
config.py
Zentrales Konfigurationsmodul für das ArgusGrid Projekt.
Verwaltet API-Keys und Energiemarkt-Ländercodes (EIC).
"""

import os
from pathlib import Path

# Basis-Pfade im Projekt
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# API-Konfiguration (Sicherheits-Best-Practice)
ENTSOE_API_TOKEN = os.environ.get("ENTSOE_API_TOKEN", "d0168f23-7637-489f-9333-9471a58cd8ef")

# Wichtige EIC (Energy Identification Codes) für Cross-Border Analysen
MARKET_AREAS = {
    "AT": "10YAT-APG------L",     # Marktgebiet Österreich (APG)
    "CH": "10YCH-SWISSGRIDZ",      # Marktgebiet Schweiz
    "DE_LU": "10Y1001A1001A82H",  # Marktgebiet Deutschland / Luxemburg
    "FR": "10YFR-RTE------C",     # Marktgebiet Frankreich
}

# Modell-Hyperparameter für den TensorFlow Autoencoder
MODEL_CONFIG = {
    "latent_dim": 8,
    "epochs": 50,
    "batch_size": 32,
    "contamination_rate": 0.01  # Erwartete Anomalie-Quote (1%) für den Schwellenwert
}