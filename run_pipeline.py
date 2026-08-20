import logging
from pathlib import Path
import pandas as pd

from config.config import ENTSOE_API_TOKEN, MARKET_AREAS
from src.data_pipeline.errors import APIConnectionError, DataValidationError
from src.data_pipeline.entsoe_loader import ENTSO_E_Loader

# Root-Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("ArgusGrid")

def run_live_test():
    logger.info("Starte ArgusGrid Live-API Test...")

    # 1. Loader initialisieren und Token + AT-Ländercode aus der Config injizieren
    loader = ENTSO_E_Loader(api_key=ENTSOE_API_TOKEN, country_code=MARKET_AREAS["AT"])
    logger.info(f"Loader erfolgreich gestartet: {loader}")

    # 2. Einen kurzen Testzeitraum definieren
    # Hinweis: ENTSO-E verlangt Zeitzonen, wie z.B. "Europe/Vienna"
    start_time = pd.Timestamp("2026-07-01", tz="Europe/Vienna")
    end_time = pd.Timestamp("2026-07-03", tz="Europe/Vienna")

    try:
        logger.info("Rufe Live-Daten von der ENTSO-E Plattform ab...")
        # 3. Daten extrahieren
        df = loader.extract_data(start=start_time, end=end_time)
        
        # 4. Erfolg ausgeben
        logger.info("🎉 ERFOLG! Daten erfolgreich gestreamt und validiert.")
        print("\n--- Die ersten Zeilen des Live-Strommixes ---")
        print(df.head())
        print(f"\nGesamte extrahierte Zeilen: {len(df)}")


    except Exception as e:
        logger.error(f"❌ Test fehlgeschlagen! Kritischer Fehler in der Pipeline: {e}")

if __name__ == "__main__":
    run_live_test()