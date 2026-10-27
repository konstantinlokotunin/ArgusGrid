"""
extraction.py
Historische Datenbeschaffung (Extraction Layer) für die ArgusGrid-Pipeline.
Optimiert auf minimale API-Requests durch jahresbasierte Block-Abfragen.
"""

import logging
from typing import List, Optional
import pandas as pd

from config.config import ENTSOE_API_TOKEN, MARKET_AREAS
from src.data_pipeline.entsoe_loader import ENTSO_E_Loader
from src.data_pipeline.entsog_loader import ENTSO_G_Loader

logger = logging.getLogger("ArgusGrid")

class DataPipeline:
    """Ermöglicht die Auswertung mehrjähriger Energiedatenströme über mehrere EU-Märkte hinweg."""
    
    def __init__(self):
        # Stromzonen für mehrere Märkte (Anpassung je nach verfügbaren Konfigurationsschlüsseln)
        self.market_zones = ["AT", "BE", "DE_LU", "FR", "IT", "NL"]
        # Gas-Knotenpunkte für mehrere Märkte (Anpassung je nach verfügbaren Konfigurationsschlüsseln)
        self.gas_points = ["Baumgarten", "Tarvisio / Arnoldstein", "Zevenaar (OGE)", "Bocholtz (OGE)"]

    def generate_yearly_intervals(self, years: int) -> pd.DatetimeIndex:
        """
        Erstellt ein sequenzielles Array mit jährlichen Startgrenzen für das API-Scraping in Blöcken.
        """
        # Wir starten vom aktuellen Tag und gehen X Jahre zurück
        end_point = pd.Timestamp.now().normalize()
        start_point = end_point - pd.DateOffset(years=years)
        return pd.date_range(start=start_point, end=end_point, freq="YS")

        # -------------------------------------------------------------------------
        # PIPELINE 1: Historische ENTSO-E Daten (Österreich, Deutschland, Frankreich, Italien, Niederlande, Belgien, Luxemburg)
        # -------------------------------------------------------------------------

    def get_power_data(self, years: int, zone: Optional[str] = None) -> List[pd.DataFrame]:
        """
        Erlaubt entweder den Abruf aller Zonen oder einer spezifischen Zone (für Parallelisierung).
        """
        logger.info("--- Phase 1: Sammle historische Stromdaten (ENTSO-E) ---")

        # Generiere Jahresgrenzen (Europe/Vienna Zeitzone für ENTSO-E spezifizieren)
        end_point = pd.Timestamp.now().normalize()
        start_point = end_point - pd.DateOffset(years=years)

        # Wir erstellen eine Liste von Start- und Endpaaren für die Jahre
        yearly_bounds = []
        current_start = start_point
        while current_start < end_point:
            current_end = min(current_start + pd.DateOffset(years=1), end_point)
            yearly_bounds.append((current_start.tz_localize("Europe/Vienna"), current_end.tz_localize("Europe/Vienna")))
            current_start = current_end

        all_extracted_chunks = []
        
        for zone in self.market_zones:
            # Safe lookup in config.py
            country_code = MARKET_AREAS.get(zone, zone)
            try:
                e_loader = ENTSO_E_Loader(api_key=ENTSOE_API_TOKEN, country_code=country_code)
            except Exception as e:
                logger.error(f"Failed to initialize ENTSO-E loader for zone {zone}: {e}")
                continue
        
            for i in range(len(months) - 1):
                m_start = months[i]
                m_end = months[i+1]
                try:
                    raw_data = e_loader.extract_data(start=m_start, end=m_end)
                    if not raw_data.empty:
                        # Append metadata column to prevent tracking collision during merge
                        raw_data["market_zone"] = zone
                        all_extracted_chunks.append(raw_data)
                except Exception as e:
                    logger.warning(f"Zeitintervall {m_start.strftime('%m/%Y')} übersprungen wegen Fehler: {e}.")
                    continue

        return all_extracted_chunks

        # -------------------------------------------------------------------------
        # PIPELINE 2: Historische ENTSO-G Daten (Österreich, Deutschland, Niederlande)
        # -------------------------------------------------------------------------

    def get_gas_data(self, years: int) -> List[pd.DataFrame]:
        """
        Scrapes physical pipeline flow metrics across major international gas entry routes.
        """
        logger.info("--- Phase 2: Sammle historische Gasdaten (ENTSO-G) ---")
        months = self.generate_monthly_intervals(years)
        all_extracted_chunks = []

        for point in self.gas_points:
            # Instantiating a clean loader per targeted node
            try:
                g_loader = ENTSO_G_Loader(point_label=point, direction='Entry')
            except Exception as e:
                logger.error(f"Failed to initialize ENTSO-G loader for point {point}: {e}")
                continue
        
            for i in range(len(months) - 1):
                m_start = months[i]
                m_end = months[i+1]
            
                try:
                    logger.info(f"Lade Gasdaten für den folgenden Zeitintervall: {m_start.strftime('%m/%Y')}")
                    raw_data = g_loader.extract_data(start=m_start.tz_localize(None), end=m_end.tz_localize(None))
                    if not raw_data.empty:
                        all_extracted_chunks.append(raw_data)
                except Exception as e:
                    logger.warning(f"Zeitintervall {m_start.strftime('%m/%Y')} übersprungen wegen Fehler: {e}.")
                    continue

        return all_extracted_chunks