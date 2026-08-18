"""
main.py
Der zentrale Einstiegspunkt für die ETL-Pipeline des ESG Data Sentinel.
Orchestriert das Laden, Bereinigen und Transformieren der Emissionsdaten.
"""

import logging
from pathlib import Path
import pandas as pd

from src.pipeline.errors import InvalidFileFormat, DataValidationError, EmptyDatasetError
from src.pipeline.extract import DataLoader
from src.pipeline.cleaning import DataCleaner
from src.ml.transform import DataTransformer

# Root-Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("ESG_Sentinel_Core")

def calculate_missing_report(df: pd.DataFrame) -> pd.DataFrame:
    """Reine Hilfsfunktion: Erstellt eine Übersicht fehlender Werte ohne Seiteneffekte."""
    return pd.DataFrame({
        "missing_values": df.isna().sum(),
        "missing_percent": round(df.isna().mean() * 100, 2)
    }).sort_values("missing_values", ascending=False)

class ETLPipeline:
    """
    Führt die ETL-Pipeline (inkl. Rohdatenbeschaffung, -bereinigung & -transformation) geschützt aus und
    protokolliert jeden Teilschritt. Baut über Komposition die ETL-Pipeline aus den spezialisierten Unterklassen auf.
    """ 
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.input_file = self.base_dir / "data" / "raw" / "industrial_releases_of_pollutants_to_air.csv"
        self.output_missing_csv = self.base_dir / "outputs" / "reports" / "missing_data_report.csv"

        # --- KOMPOSITION (RAG-Architektur-Style) ---
        self.loader = DataLoader(self.input_file)
        # Cleaner und Transformer werden nach dem Laden der Daten injiziert
        self.cleaner = None
        self.transformer = None

    def execute_etl(self) -> pd.DataFrame:
        """Führt die ETL-Pipeline geschützt aus und persistiert die bereinigten Features."""
        logger.info("=== ESG Data Sentinel ETL-Pipeline gestartet ===")

        try:
            # --- PHASE 1: EXTRACTION (Generator-Streaming) ---
            logger.info("Schritt 1: Extrahiere Rohdaten über Lazy-Evaluation-Generatoren...")
            df_raw = self.loader.extract_data()
            logger.info(f"Rohdaten erfolgreich geladen. Dimensionen: {df_raw.shape}")

            # --- PHASE 2: MISSING DATA REPORT (Reine Berechnung) ---
            logger.info("Schritt 2: Analysiere fehlende Werte...")
            df_missing = calculate_missing_report(df_raw)
            self.output_missing_csv.parent.mkdir(parents=True, exist_ok=True)
            df_missing.to_csv(self.output_missing_csv, index=True)
            logger.info(f"Missing-Report erfolgreich exportiert nach: \"{self.output_missing_csv}\".")

            # --- PHASE 3: CLEANING ---
            logger.info("Schritt 3: Führe eine Filterung und Bereinigung der Datensätze durch...")
            self.cleaner = DataCleaner(df_raw)
            df_cleaned = self.cleaner.clean_data()
            logger.info(f"Daten erfolgreich bereinigt. Dimensionen: {df_cleaned.shape}")

            # --- PHASE 4: FEATURE ENGINEERING ---
            logger.info("Schritt 4: Führe Schadstoff-Klassifizierung und Feature Engineering durch...")
            self.transformer = DataTransformer(df_cleaned)
            df_transformed = self.transformer.transform_data()
            logger.info(f"Schadstoff-Klassifizierung und Feature Engineering abgeschlossen. Dimensionen: {df_transformed.shape}")

            logger.info("=== ETL-Pipeline erfolgreich und fehlerfrei beendet ===")

        # --- ROBUSTE FEHLERBEHANDLUNG ---
        except InvalidFileFormat as e:
            logger.error(f"Pipeline-Abbruch: Ungültiges Dateiformat erkannt -> {e}")
        except EmptyDatasetError as e:
            logger.error(f"Pipeline-Abbruch: Keine Daten nach der Filterung übrig -> {e}")
        except DataValidationError as e:
            logger.error(f"Pipeline-Abbruch: Validierungsfehler im Datenstrom -> {e}")
        except Exception as e:
            logger.critical(f"Unerwarteter Systemfehler: {e}", exc_info=True)

        return df_transformed

if __name__ == "__main__":
    pipeline = ETLPipeline()
    pipeline.execute_etl()