"""
cleaning.py
Reine funktionale Hilfswerkzeuge zur Bereinigung von ENTSO-Energiedatenreihen.
Ohne Seiteneffekte und optimiert für die Zeitreihen-Anomalieerkennung.
"""

import logging
import pandas as pd
from .errors import DataValidationError

logger = logging.getLogger("ArgusGrid")

def clean_and_harmonize(df: pd.DataFrame, expected_freq: str = "h") -> pd.DataFrame:
    """
    Entfernt Duplikate, erstellt ein kontinuierliches Zeitraster und füllt Lücken via Interpolation.
    Gibt ein bereinigtes DataFrame mit einem eindeutig benannten Index zurück.
    """

    # 1. Duplikate basierend auf dem Index (Zeitstempel) entfernen
    initial_len = len(df)
    df = df[~df.index.duplicated(keep="last")].sort_index()
    
    if len(df) < initial_len:
        logger.warning(f"Duplikat-Bereinigung: {initial_len - len(df)} doppelte Zeitstempel entfernt.")

    # 2. Resampling auf ein mathematisch homogenes Stundenraster für den AutoEncoder
    try:
        full_range = pd.date_range(start=df.index.min(), end=df.index.max(), freq=expected_freq)
        df = df.reindex(full_range)
    except Exception as e:
        raise DataValidationError(f"Erstellung des homogenen Zeitrasters fehlgeschlagen: {e}")

    # 3. Fehlende Werte über vektorisierte lineare Interpolation bereinigen
    df = df.interpolate(method="linear").ffill().bfill()
    df.index.name = "timestamp"
    
    return df