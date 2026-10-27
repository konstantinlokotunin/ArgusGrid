"""
storage.py
Modul zur persistenten Speicherung von bereinigten Zeitreihen im Parquet-Format.
Sichert die Einhaltung der Datentypen und optimiert den Speicherplatz.
"""

import logging
from pathlib import Path
import pandas as pd

# Nutzt den einheitlichen Projektnamen für das Logging
logger = logging.getLogger("ArgusGrid")

def save_data(df: pd.DataFrame, file_path: str | Path) -> None:
    """
    Speichert ein Pandas-DataFrame komprimiert als Apache Parquet Datei.
    Erstellt automatisch notwendige Ordnerstrukturen.
    """
    if df.empty:
        logger.warning("Speichern abgebrochen: Das übergebene DataFrame ist leer.")
        return

    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # compression='snappy' ist der Industrie-Standard für schnelles Lesen/Schreiben
        df.to_parquet(path, engine='fastparquet', compression='snappy')
        
        # Dateigröße zur Kontrolle ermitteln (für Ihre 30-MB-Anforderung wichtig!)
        file_size = path.stat().st_size / (1024 * 1024)
        logger.info(f"Datei erfolgreich gespeichert: {path.name} ({file_size:.2f} MB, {len(df)} Zeilen)")
        
    except Exception as e:
        logger.error(f"Fehler beim Schreiben der Parquet-Datei {path}: {e}")
        raise