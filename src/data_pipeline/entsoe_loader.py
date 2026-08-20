"""
entsoe_loader.py
Liest Stromdaten via API und streamt sie zeilenweise über einen nativen Generator.
Fehlerhafte Zeilen werden übersprungen, damit die Datenpipeline nicht abbricht.
"""

import logging
import pandas as pd
from .errors import APIConnectionError, DataValidationError
from entsoe.entsoe import EntsoePandasClient
from typing import Generator, Dict, Any

# Nutzt den einheitlichen Projektnamen für das Logging
logger = logging.getLogger("ArgusGrid")

class ENTSO_E_Loader:
    """Komponente zum zeilenweisen Streamen von Live-Stromdaten der ENTSO-E Transparency Plattform."""

    def __init__(self, api_key: str, country_code: str):
        self.client = EntsoePandasClient(api_key=api_key)
        self.country_code = country_code

    @staticmethod
    def validate_row(row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pure Function: Validiert eine einzelne Datenzeile ohne Seiteneffekte.
        Prüft, ob der Datensatz vollständig leer oder beschädigt ist.
        """
        if not row:
            raise DataValidationError("Leere Zeile empfangen.")

        # Falls alle Stromerzeugungswerte NaN (keine Daten) sind, überspringen wir die Zeile
        cleaned_values = [v for k, v in row.items() if k != 'timestamp']
        if all(v is None or pd.isna(v) for v in cleaned_values):
            raise DataValidationError("Datensatz enthält nur fehlende Werte (NaN).")
            
        return row

    def stream_data(self, start: pd.Timestamp, end: pd.Timestamp) -> Generator[Dict, None, None]:
        """
        Interner Lazy-Evaluation Generator.
        Holt den Datenblock ab und nutzt 'yield', um jede Zeile einzeln im Speicher zu halten.
        """
        try:
            # Abruf der tatsächlichen Stromerzeugung je Kraftwerkstyp
            df = self.client.query_generation(self.country_code, start=start, end=end)
        except Exception as e:
            raise APIConnectionError(f"Verbindung zur ENTSO-E Plattform fehlgeschlagen: {e}")

        # 1. Spalten-Struktur eindeutig und flach machen
        # Wir verbinden die Ebenen (z.B. "Fossil Gas" und "Actual Generation") zu "Fossil Gas_Actual Generation"
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [f"{col[0]}_{col[1]}" if str(col[1]) != 'nan' else col[0] for col in df.columns]

        # 2. Den Zeit-Index in eine saubere Spalte namens 'timestamp' umwandeln
        df = df.rename_axis('timestamp').reset_index()
        
        # 3. Zeitzone entfernen oder in Text umwandeln, damit es beim JSON-Export nicht crasht
        df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')

        # Zeilenweise als Stream ausgeben (Lazy Evaluation)
        for record in df.to_dict(orient='records'):
            try:
                valid_record = self.validate_row(record)
                yield valid_record
            except DataValidationError as e:
                logger.warning(f"Korrupte ENTSO-E Zeile übersprungen: {e}")
                continue

    def extract_data(self, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
        """
        Sammelt alle fehlerfreien Zeilen aus dem Lazy-Evaluation Generator und baut das DataFrame.
        """
        valid_rows = []
        generator = self.stream_data(start, end)

        while True:
            try:
                entry = next(generator)
                valid_rows.append(entry)
            except StopIteration:
                # Normales Ende des Generators erreicht
                break
            except Exception as e:
                logger.error(f"Kritischer Fehler in der Data-Streaming-Pipeline: {e}")
                continue

        if not valid_rows:
            raise DataValidationError("Keine validen ENTSO-E Daten für diesen Zeitraum abrufbar.")

        # Konvertierung in ein DataFrame für die nachfolgende Transformation
        return pd.DataFrame(valid_rows).set_index("timestamp")

    def __repr__(self) -> str:
        return f"ENTSO_E_Loader(area_id='{self.country_code}')"