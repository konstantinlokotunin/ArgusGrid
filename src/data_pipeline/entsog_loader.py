"""
entsog_loader.py
Liest Gasdaten via REST-API und streamt sie zeilenweise über einen nativen Generator.
Korrupte Zeilen werden übersprungen, damit die Datenpipeline nicht abbricht.
"""

import logging
import requests
import pandas as pd
from .errors import APIConnectionError, DataValidationError
from typing import Generator, Dict, Any

# Nutzt den einheitlichen Projektnamen für das Logging
logger = logging.getLogger("ArgusGrid")

class ENTSO_G_Loader:
    """Klasse zum zeilenweisen Streamen von Live-Gasdaten der ENTSO-G Transparency Plattform."""

    # Die offizielle, öffentliche Basis-URL der ENTSOG-API
    BASE_URL = "https://transparency.entsog.eu/api/v1/operationaldatas"

    def __init__(self, point_label: str, direction: str = 'Entry'):
        """
        point_label: Name des Gas-Knotenpunkts (z.B. 'Baumgarten')
        direction: 'Entry' (Import) oder 'Exit' (Export)
        """
        self.point_label = point_label
        self.direction = direction

    @staticmethod
    def validate_row(row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prüft die Zeilenstruktur, ohne Messwerte zu verändern oder zu löschen.
        """
        if not row:
            raise DataValidationError("ENTSO-G: Eine Datenzeile muss ein nicht leeres Dictionary sein.")

        if "timestamp" not in row:
            raise DataValidationError("ENTSO-G: In einer Datenzeile fehlt der Zeitstempel.")

        if len(row) < 5:
            raise DataValidationError("ENTSO-G: In einer Datenzeile fehlen notwendige Features.")
        
        raw_value = row.get("value")
        if raw_value is None or raw_value == "":
            raise DataValidationError("ENTSO-G: Die Datenzeile enthält keine Messwerte.")

        try:
            row["value"] = float(raw_value)
        except (ValueError, TypeError):
            raise DataValidationError(f"Nicht-numerischer Messwert erkannt: {raw_value}")
            
        return row

    def stream_data(self, start: pd.Timestamp, end: pd.Timestamp) -> Generator[Dict[str, Any], None, None]:
        """
        Interner Lazy-Evaluation Generator.
        Fragt die REST-API ab und nutzt 'yield', um jede Zeile einzeln im Speicher zu halten.
        Akzeptiert einheitlich pandas Timestamps wie der Strom-Loader.
        """

        # Eingaben müssen echte Zeitpunkte ohne einer bekannten Zeitzone sein.
        for timestamp in (start, end):
            if not isinstance(timestamp, pd.Timestamp) or pd.isna(timestamp):
                raise DataValidationError("ENTSO-G: Start- und Enddatum müssen gültige pandas-Zeitpunkte sein.")

        if start >= end:
            raise DataValidationError("ENTSO-G: Das Startdatum muss vor dem Enddatum liegen.")

        # API verlangt reines Datumsformat YYYY-MM-DD als Text
        params = {
            "from": start.strftime("%Y-%m-%d"),
            "to": end.strftime("%Y-%m-%d"),
            "limit": -1,                  
            "indicator": "Physical Flow", 
            "pointLabel": self.point_label,
            "directionKey": self.direction.lower()
        }

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=15)
            response.raise_for_status()   
            raw_data = response.json() 
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der ENTSO-G Daten: {e}")
            raise APIConnectionError("ENTSO-G: Datenabruf fehlgeschlagen; Netzwerk, Token und Zeitraum prüfen.") from e

        # Unerwartete Fehler werden weitergegeben und nicht als leeres Ergebnis behandelt.
        if not isinstance(raw_data, Dict):
            raise DataValidationError("ENTSO-G lieferte kein DataFrame.")
        if not raw_data:
            raise DataValidationError("ENTSO-G lieferte keine Beobachtungen.")

        raw_items = raw_data.get("operationaldatas", [])


        for item in raw_items:
            try:
                record = {
                    'timestamp': item.get('periodFrom'),
                    'point': item.get('pointLabel'),
                    'value': item.get('value'),
                    'unit': item.get('unit'),
                    'status': item.get('indicator')
                }
                yield self.validate_row(record)
            except DataValidationError as e:
                logger.warning(f"Korrupte ENTSO-G Zeile übersprungen: {e}")
                continue

    def extract_data(self, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
        """
        Sammelt alle nicht korrupten Zeilen aus dem Lazy-Evaluation Generator und baut das DataFrame.
        """
        valid_rows = []

        try:
            for entry in self.stream_data(start, end):
                valid_rows.append(entry)
        except Exception as e:
            logger.error(f"Kritischer Fehler in der Gas-Streaming Pipeline: {e}")

        if not valid_rows:
            raise DataValidationError("Keine validen ENTSO-G Daten für diesen Zeitraum abrufbar.")

        df = pd.DataFrame(valid_rows)
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        return df.set_index("timestamp").sort_index()

    def __repr__(self) -> str:
        return f"ENTSO_G_Loader(point='{self.point_label}', direction='{self.direction}')"