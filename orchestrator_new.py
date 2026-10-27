"""
orchestrator.py
Zentraler Pipeline-Orchestrator für das ArgusGrid-System.
Verbindet Extraktion, spaltenbasierte Zusammenführung, Bereinigung und Speicherung zu einer stabilen ETL-Kette.
Optimierte Hochleistungs-Variante mi Thread-Parallelisierung und Vor-Harmonisierung.
"""
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List
import pandas as pd

from src.data_pipeline.extraction import DataPipeline
from src.data_pipeline.cleaning import clean_and_harmonize
from src.data_pipeline.storage import save_data
from src.data_pipeline.errors import APIConnectionError, DataValidationError

# Konfiguration eines übersichtlichen Konsolen-Loggings
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger("ArgusGrid")


class PipelineOrchestrator:
    """Steuert den sequenziellen Ablauf der Datenbeschaffung und -aufbereitung."""

    def __init__(self, target_path: str = "data/silver"):
        self.loader = DataPipeline()
        self.countries = self.loader.market_zones
        self.target_path = Path(target_path)
        self.target_path.mkdir(parents=True, exist_ok=True)

    def _fetch_single_country_year(self, country: str, year_offset: int) -> List[pd.DataFrame]:
        """Hilfsmethode für den isolierten Netzwerk-Abruf eines Landes (für Threads geeignet)."""
        try:
            logger.info(f"[API Abruf] Starte Download für Land: {country}")
            # HINWEIS: Falls dein Extraction-Modul das Argument 'country' oder 'market_zone' 
            # noch nicht isoliert unterstützt, sollte dies dort dringend implementiert werden!
            return self.loader.get_power_data(years=1, zone=country) 
        except Exception as e:
            logger.error(f"Fehler beim API-Abruf für {country}: {e}")
            return []

    def _prepare_raw_data(self, chunks: List[pd.DataFrame]) -> pd.DataFrame:
        """Führt Chunks zusammen und stellt sicher, dass ein gültiger Zeitstempel-Index existiert."""
        start_time = time.time()
        logger.info(f"Führe {len(chunks)} Chunks via pd.concat zusammen...")
        df_raw = pd.concat(chunks, axis=0)
        logger.info(f"Concat abgeschlossen in {time.time() - start_time:.2f} Sekunden.")

        # Falls kein DatetimeIndex vorliegt, konvertieren wir die 'timestamp'-Spalte aktiv
        if not isinstance(df_raw.index, pd.DatetimeIndex):
            if "timestamp" in df_raw.columns:
                logger.info("Konvertiere 'timestamp'-Spalte zu einem DatetimeIndex...")
                df_raw["timestamp"] = pd.to_datetime(df_raw["timestamp"])
                df_raw = df_raw.set_index("timestamp")
            else:
                raise DataValidationError("Rohdaten enthalten weder einen DatetimeIndex noch eine 'timestamp'-Spalte.")
        
        # Namen des Index für das spätere Pivoting explizit festlegen
        df_raw.index.name = "timestamp"
        return df_raw

    def _clean_string_for_tensorflow(self, text: str) -> str:
        """Entfernt Sonderzeichen aus Spaltennamen für die TensorFlow-Kompatibilität."""
        return text.replace(' ', '_').replace('/', '_').replace('(', '').replace(')', '')

    def _pivot_power_data(self, df_raw: pd.DataFrame) -> pd.DataFrame:
        """Führt das rechenintensive Pivoting mit explizitem Zeit-Tracking durch."""
        start_time = time.time()
        logger.info("Starte pivot_table-Operation für Stromdaten (CPU-intensiv)...")

        if "Actual Generation Output" in df_raw.columns:
            df_pivot = df_raw.pivot_table(
                index="timestamp", 
                columns="market_zone", 
                values="Actual Generation Output", 
                aggfunc="last"
            )
            # Spaltennamen bereinigen
            df_pivot.columns = [f"{self._clean_string_for_tensorflow(str(col))}_power_generation" for col in df_pivot.columns]
        else:
            # Sicherer Fallback für MultiIndex-Spalten inklusive TF-Bereinigung
            df_pivot = df_raw.pivot_table(index="timestamp", columns="market_zone", aggfunc="last")
            df_pivot.columns = [
                f"{self._clean_string_for_tensorflow(str(zone))}_{col}" 
                for col, zone in df_pivot.columns
            ]

        logger.info(f"Pivoting abgeschlossen in {time.time() - start_time:.2f} Sekunden.")
        return df_pivot

    def run_e_pipeline(self, years: int) -> None:
        """Extrahiert, strukturiert, bereinigt und speichert die historische Strom-Zeitreihe."""
        logger.info(f"=== Starte ETL-Prozess: historische ENTSO-E Daten für {years} Jahre ===")

        # Optimierung: Wir laden und verarbeiten die Daten jahrweise, um den RAM zu schonen
        pivoted_years = []

        for current_year in range(1, years + 1):
            logger.info(f"--- Verarbeite Jahr {current_year} von {years} ---")
            try:
                all_extracted_chunks = self.loader.get_power_data(years=years)
            except APIConnectionError as err:
                logger.error(f"Strom-Pipeline abgebrochen bei Jahr {current_year}: {err}.")
                raise

            if not all_extracted_chunks:
                logger.warning(f"Keine Daten für Jahr {current_year} empfangen.")
                continue

            df_raw = self._prepare_raw_data(all_extracted_chunks)
            pivoted_years.append(self._pivot_power_data(df_raw))

        if not pivoted_years:
            raise DataValidationError("Strom-Pipeline abgebrochen: Keine historischen Strom-Rohdaten empfangen.")

        # Zusammenführen der bereits schlanken, pivotierten Jahres-Tabellen
        logger.info("Verknüpfe pivotierte Jahres-Abschnitte...")
        df_pivot_totals = pd.concat(pivoted_years, axis=0).sort_index()

        # Bereinigung und lückenlose Stundengitter-Erstellung
        logger.info("Harmonisiere und bereinige historische Stromdaten...")
        start_clean = time.time()
        power_df = clean_and_harmonize(df_pivot_totals)
        logger.info(f"Harmonisierung abgeschlossen in {time.time() - start_clean:.2f} Sekunden.")

        target_path = self.target_path / "historische_Stromdaten.parquet"
        save_data(power_df, target_path)
        logger.info(f"=== Historische Stromdaten unter ({target_path}) gespeichert ===")

    def run_g_pipeline(self, years: int) -> None:
        """Extrahiert, strukturiert, bereinigt und speichert die historische Gas-Zeitreihe."""
        logger.info(f"=== Starte ETL-Prozess: historische ENTSO-G Daten für {years} Jahre ===")

        try:
            all_extracted_chunks = self.loader.get_gas_data(years=years)
        except APIConnectionError as err:
            logger.error(f"Gas-Pipeline abgebrochen: {err}. Keine Rohdaten extrahiert.")
            raise

        if not all_extracted_chunks:
            raise DataValidationError("Gas-Pipeline abgebrochen: Keine Rohdaten empfangen.")

        # 1. Daten konsolidieren und Zeitachse absichern
        df_raw = self._prepare_raw_data(all_extracted_chunks)

        # 2. In ein knotenbasiertes Spaltenraster transformieren (Pivoting)
        logger.info("Überführe Gasdaten in ein spaltenbasiertes Knotenpunktraster...")

        if "value" in df_raw.columns:
            df_pivot = df_raw.pivot_table(
                index="timestamp", 
                columns="point", 
                values="value", 
                aggfunc="last"
            )
            # KORREKTUR: Konsistente Nutzung der zentralen Hilfsmethode
            df_pivot.columns = [f"gas_{self._clean_string_for_tensorflow(str(col))}" for col in df_pivot.columns]
        else:
            df_pivot = df_raw.pivot_table(index="timestamp", columns="point", aggfunc="last")
            df_pivot.columns = [
                f"gas_{self._clean_string_for_tensorflow(str(point))}_{col}" 
                for col, point in df_pivot.columns
            ]

        # 3. Bereinigung und lückenlose Stundengitter-Erstellung
        logger.info("Harmonisiere und bereinige historische Gasdaten...")
        gas_df = clean_and_harmonize(df_pivot)

        target_path = self.target_path / "historische_Gasdaten.parquet"
        save_data(gas_df, target_path)
        logger.info(f"=== Historische Gasdaten unter ({target_path}) gespeichert ===")


if __name__ == "__main__":
    orchestrator = PipelineOrchestrator()
    try:
        orchestrator.run_e_pipeline(years=3)
        #orchestrator.run_g_pipeline(years=3)
    except Exception as e:
        logger.critical(f"Kritischer Fehler im Hauptprozess: {e}", exc_info=True)