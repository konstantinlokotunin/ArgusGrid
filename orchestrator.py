"""
orchestrator.py
Zentraler Pipeline-Orchestrator für das ArgusGrid-System.
Verbindet Extraktion, spaltenbasierte Zusammenführung, Bereinigung und Speicherung zu einer stabilen ETL-Kette.
"""
import logging
from pathlib import Path
from typing import List
import pandas as pd

from src.data_pipeline.extraction import DataPipeline
from src.data_pipeline.cleaning import clean_and_harmonize
from src.data_pipeline.storage import save_data
from src.data_pipeline.errors import APIConnectionError, DataValidationError

logger = logging.getLogger("ArgusGrid")

class PipelineOrchestrator:
    """Steuert den sequenziellen Ablauf der Datenbeschaffung und -aufbereitung."""

    def __init__(self, target_path: str = "data/silver"):
        self.loader = DataPipeline()
        self.target_path = Path(target_path)
        self.target_path.mkdir(parents=True, exist_ok=True)

    def _prepare_raw_data(self, chunks: List[pd.DataFrame]) -> pd.DataFrame:
        """Führt Chunks zusammen und stellt sicher, dass ein gültiger Zeitstempel-Index existiert."""
        df_raw = pd.concat(chunks, axis=0)
        
        # Falls kein DatetimeIndex vorliegt, konvertieren wir die 'timestamp'-Spalte aktiv
        if not isinstance(df_raw.index, pd.DatetimeIndex):
            if "timestamp" in df_raw.columns:
                df_raw["timestamp"] = pd.to_datetime(df_raw["timestamp"])
                df_raw = df_raw.set_index("timestamp")
            else:
                raise DataValidationError("Rohdaten enthalten weder einen DatetimeIndex noch eine 'timestamp'-Spalte.")
        return df_raw

    def _clean_string_for_tensorflow(self, text: str) -> str:
        """Entfernt Sonderzeichen aus Spaltennamen für die TensorFlow-Kompatibilität."""
        return text.replace(' ', '_').replace('/', '_').replace('(', '').replace(')', '')

    def run_e_pipeline(self, years: int) -> None:
        """Extrahiert, strukturiert, bereinigt und speichert die historische Strom-Zeitreihe."""
        logger.info(f"=== Starte ETL-Prozess: historische ENTSO-E Daten für {years} Jahre ===")

        try:
            all_extracted_chunks = self.loader.get_power_data(years=years)
        except APIConnectionError as err:
            logger.error(f"Strom-Pipeline abgebrochen: {err}. Keine Rohdaten extrahiert.")
            raise

        if not all_extracted_chunks:
            raise DataValidationError("Strom-Pipeline abgebrochen: Keine Rohdaten empfangen.")

        # 1. Daten konsolidieren und Zeitachse absichern
        df_raw = self._prepare_raw_data(all_extracted_chunks)

        # 2. Überführung in ein regionales Spaltenraster (Pivoting)
        logger.info("Überführe Stromdaten in ein multi-regionales Spaltenraster...")

        # Falls die ENTSO-E Antwort eine Spalte 'Actual Generation Output' hat, nutzen wir diese,
        # andernfalls nehmen wir alle numerischen Spalten und hängen die Marktzone an.
        if "Actual Generation Output" in df_raw.columns:
            df_pivot = df_raw.pivot_table(
                index=df_raw.index, 
                columns="market_zone", 
                values="Actual Generation Output", 
                aggfunc="last"
            )
            # Spaltennamen bereinigen
            df_pivot.columns = [f"gas_{self._clean_string_for_tensorflow(str(col))}" for col in df_pivot.columns]
        else:
            # Sicherer Fallback für MultiIndex-Spalten inklusive TF-Bereinigung
            df_pivot = df_raw.pivot_table(index=df_raw.index, columns="point", aggfunc="last")
            df_pivot.columns = [
                f"gas_{self._clean_string_for_tensorflow(str(point))}_{col}" 
                for col, point in df_pivot.columns
            ]

        # 3. Bereinigung und lückenlose Stundengitter-Erstellung auf den pivotierten Daten
        logger.info(f"Harmonisiere und bereinige Stromdaten...")

        power_df = clean_and_harmonize(df_pivot)
        
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
        # Wir trennen die Werte nach Gas-Knotenpunkten auf (Spalten: Baumgarten, Tarvisio / Arnoldstein, etc.)
        logger.info("Überführe Gasdaten in ein spaltenbasiertes Knotenpunktraster...")

        # Falls die ENTSO-G Antwort eine Spalte 'Value' hat, nutzen wir diese,
        # andernfalls nehmen wir alle numerischen Spalten und hängen die Gas-Knotenpunkte an.
        if "value" in df_raw.columns:
            df_pivot = df_raw.pivot_table(
                index=df_raw.index, 
                columns="point", 
                values="value", 
                aggfunc="last"
            )
            # Spaltennamen für TensorFlow bereinigen (Sonderzeichen entfernen)
            cleaned_cols = []
            for col in df_pivot.columns:
                safe_name = str(col).replace(' ', '_').replace('/', '_').replace('(', '').replace(')', '')
                cleaned_cols.append(f"gas_{safe_name}")
            df_pivot.columns = cleaned_cols
        else:
            # Schneller, lesbarer Fallback für alle numerischen Spalten
            df_pivot = df_raw.pivot_table(index=df_raw.index, columns="point", aggfunc="last")
            df_pivot.columns = [f"gas_{point}_{col}" for col, point in df_pivot.columns]

        # 3. Bereinigung und lückenlose Stundengitter-Erstellung auf den pivotierten Daten
        logger.info(f"Harmonisiere und bereinige Gasdaten...")

        gas_df = clean_and_harmonize(df_pivot)

        target_path = self.target_path / "historische_Gasdaten.parquet"
        save_data(gas_df, target_path)
        logger.info(f"=== Historische Gasdaten unter ({target_path}) gespeichert ===")

if __name__ == "__main__":
    # Einfache Logging-Aktivierung für lokale Testläufe
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    
    orchestrator = PipelineOrchestrator()
    try:
        orchestrator.run_e_pipeline(years=1)
        orchestrator.run_g_pipeline(years=1)
    except Exception as e:
        logger.critical(f"Kritischer Fehler im Hauptprozess: {e}", exc_info=True)