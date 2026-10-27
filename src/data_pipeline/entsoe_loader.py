"""
entsoe_loader.py
Liest Stromdaten via entsoe-py Bibliothek hochperformant und rein vektoriell.
Fehlerhafte Zeilen werden übersprungen, damit die Datenpipeline nicht abbricht.
"""

import logging
import pandas as pd
from .errors import APIConnectionError, DataValidationError
from entsoe.entsoe import EntsoePandasClient

# Nutzt den einheitlichen Projektnamen für das Logging
logger = logging.getLogger("ArgusGrid")

class ENTSO_E_Loader:
    """Klasse zum zeilenweisen Streamen von Live-Stromdaten der ENTSO-E Transparency Plattform."""
    
    def __init__(self, api_key: str, country_code: str):
        self.client = EntsoePandasClient(api_key=api_key)
        self.country_code = country_code
    
    def _validate_and_clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validiert und bereinigt die DataFrame-Struktur blitzschnell auf einen Schlag (vektoriell).
        """
        if not isinstance(df, pd.DataFrame):
            raise DataValidationError("ENTSO-E lieferte kein gültiges DataFrame-Objekt.")
        if df.empty:
            raise DataValidationError("ENTSO-E lieferte ein leeres Ergebnis (keine Beobachtungen).")
        
    def stream_data(self, start: pd.Timestamp, end: pd.Timestamp) -> Generator[Dict, None, None]:
        """
        Interner Lazy-Evaluation Generator.
        Holt den Datenblock ab und nutzt "yield", um jede Zeile einzeln im Speicher zu halten.
        """
        # Eingaben müssen echte Zeitpunkte mit einer bekannten Zeitzone sein.
        for timestamp in (start, end):
            if not isinstance(timestamp, pd.Timestamp) or pd.isna(timestamp):
                raise DataValidationError("ENTSO-E: Start und Ende müssen gültige pandas-Zeitpunkte sein.")
            if timestamp.tzinfo is None:
                raise DataValidationError("ENTSO-E: Start und Ende benötigen eine Zeitzone.")

        if start >= end:
            raise DataValidationError("ENTSO-E: Das Anfangsdatum muss vor dem Enddatum liegen.")

        start = start.tz_convert("UTC")
        end = end.tz_convert("UTC")

        try:
            df = self.client.query_generation(self.country_code, start=start, end=end)
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der ENTSO-E Daten: {e}")
            raise APIConnectionError("ENTSO-E: Datenabruf fehlgeschlagen; Netzwerk, Token und Zeitraum prüfen.") from e

        # Unerwartete Fehler werden weitergegeben und nicht als leeres Ergebnis behandelt.
        if not isinstance(df, pd.DataFrame):
            raise DataValidationError("ENTSO-E lieferte kein DataFrame.")
        if df.empty:
            raise DataValidationError("ENTSO-E lieferte keine Beobachtungen.")

        df = df.copy()

        # MultiIndex Handling falls Spalten hierarchisch sind (z.B. Actual Consumption vs Generation)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [f"{col[0]}_{col[1]}" if col[1] and not pd.isna(col[1]) else col[0] for col in df.columns]

        # Zeitstempel aus dem Index als Spalte verfügbar machen
        df = df.reset_index().rename(columns={df.index.name or 'index': 'timestamp'})

        # Jede Zeile einzeln umwandeln ohne Liste im Speicher anzulegen
        for values in df.itertuples(index=False, name=None):
            record = dict(zip(df.columns, values))
            try:
                yield self.validate_row(record)
            except DataValidationError as e:
                logger.warning(f"Fehler beim Laden der ENTSO-E Daten: {e}")
                continue

    def extract_data(self, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
        """
        Sammelt alle Zeilen aus dem Lazy-Evaluation Generator und baut das DataFrame.
        """
        valid_rows = []

        try:
            for entry in self.stream_data(start, end):
                valid_rows.append(entry)
        except Exception as e:
            logger.error(f"Kritischer Fehler in der Strom-Streaming Pipeline: {e}")

        if not valid_rows:
            raise DataValidationError("Keine validen ENTSO-E Daten für diesen Zeitraum abrufbar.")
        
        df = pd.DataFrame(valid_rows)
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        return df.set_index("timestamp").sort_index()

    def __repr__(self) -> str:
        return f"ENTSO_E_Loader(country_code='{self.country_code}')"