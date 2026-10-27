"""
run_pipeline.py
Testet und startet sequenziell die Live-Pipelines für die Datenplattformen
ENTSO-E (Strom) und ENTSO-G (Gas) über identische OOP-Schnittstellen.
"""

import logging
import pandas as pd

from config.config import ENTSOE_API_TOKEN, MARKET_AREAS
from src.data_pipeline.entsoe_loader import ENTSO_E_Loader
from src.data_pipeline.entsog_loader import ENTSO_G_Loader
from src.data_pipeline.errors import APIConnectionError, DataValidationError

# Konfiguration eines übersichtlichen Konsolen-Loggings
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("ArgusGrid")

def run_data_pipeline():
    logger.info("==============================================")
    logger.info("       STARTE ARGUSGRID SYSTEMTEST            ")
    logger.info("==============================================")

    # -------------------------------------------------------------------------
    # PIPELINE 1: ENTSO-E Strom-Stream (Österreich)
    # -------------------------------------------------------------------------
    logger.info("--- Phase 1: Initialisierung Strom-Pipeline ---")

    # 1. Loader initialisieren und Token + AT-Ländercode aus der Config injizieren
    e_loader = ENTSO_E_Loader(api_key=ENTSOE_API_TOKEN, country_code=MARKET_AREAS["AT"])
    logger.info(f"Loader erfolgreich gestartet: {e_loader}")

    # Zeiträume mit korrekter Zeitzone definieren
    # Hinweis: ENTSO-E verlangt Zeitzonen, wie z.B. "Europe/Vienna"
    e_start = pd.Timestamp("2026-07-01", tz="Europe/Vienna")
    e_end = pd.Timestamp("2026-07-03", tz="Europe/Vienna")

    try:
        logger.info("Streame Live-Stromdaten von der ENTSO-E Plattform...")
        e_df = e_loader.extract_data(start=e_start, end=e_end)
        logger.info("🎉 ENTSO-E ERFOLG! Stromdaten erfolgreich gestreamt.")
        print("\n--- Auszug Strommix (Österreich) ---")
        print(e_df.head())
        print(f"Gesamtanzahl extrahierter Zeilen: {len(e_df)}\n")

    except Exception as e:
        logger.error(f"❌ ENTSO-E Pipeline fehlgeschlagen: {e}")

    # -------------------------------------------------------------------------
    # PIPELINE 2: ENTSO-G Gas-Stream (Knotenpunkt Baumgarten)
    # -------------------------------------------------------------------------
    logger.info("--- Phase 2: Initialisierung Gas-Pipeline ---")

    # Gas-Loader für den Einspeisepunkt Baumgarten (Import/Entry) starten
    g_loader = ENTSO_G_Loader(point_label='Baumgarten', direction='Entry')
    logger.info(f"Loader erfolgreich gestartet: {g_loader}")

    # Zeiträume mit korrekter Zeitzone definieren
    # Hinweis: Die ENTSO-G REST-API erwartet einfache Datums-Strings 'YYYY-MM-DD'
    g_start = pd.Timestamp("2026-07-01")
    g_end = pd.Timestamp("2026-07-03")

    try:
        logger.info("Streame Live-Gasdaten von der ENTSO-G Plattform...")
        g_df = g_loader.extract_data(start=g_start, end=g_end)
        logger.info("🎉 ENTSO-G ERFOLG! Gasdaten erfolgreich gestreamt.")
        print("\n--- Auszug Physischer Gasfluss (Baumgarten Entry) ---")
        print(g_df.head())
        print(f"Gesamtanzahl extrahierter Zeilen: {len(g_df)}\n")

    except Exception as e:
        logger.error(f"❌ ENTSO-G Pipeline fehlgeschlagen: {e}")

    logger.info("==============================================")
    logger.info("       ARGUSGRID SYSTEMTEST BEENDET           ")
    logger.info("==============================================")

if __name__ == "__main__":
    run_data_pipeline()