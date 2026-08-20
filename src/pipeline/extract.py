

"""
extract.py
Liest Rohdaten zeilenweise über einen nativen Generator ein.
Fehlerhafte Zeilen werden übersprungen, damit die Pipeline nicht abbricht.
"""

import logging
import csv
from pathlib import Path
from typing import Generator
import pandas as pd
from .errors import InvalidFileFormat, DataValidationError

logger = logging.getLogger("ESG-Data-Sentinel")

class DataLoader:
    """Komponente zum zeilenweisen Einlesen von CSV-Dateien"""

    def __init__(self, file_path: Path):
        self.file_path = file_path

    def read_rows(self) -> Generator[dict, None, None]:
        """
        Interner Lazy-Evaluation Generator.
        Nutzt 'yield', um jede Zeile einzeln im Speicher zu halten.
        """

        if self.file_path.suffix.lower() != '.csv':
            raise InvalidFileFormat(f"Nur CSV erlaubt! Erhalten: {self.file_path.suffix}")
        
        with open(self.file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Einfache Validierung: Fehlen Werte in der Zeile?
                if not row or None in row.values():
                    raise DataValidationError("Beschädigte oder unvollständige Zeile erkannt.")
                yield row
    
    def extract_data(self) -> pd.DataFrame:
        """
        Sammelt alle fehlerfreien Zeilen aus dem Lazy-Evaluation Generator.
        Fehlerhafte Zeilen werden übersprungen.
        """
        valid_rows = []
        generator = self.read_rows()
        
        while True:
            try:
                entry = next(generator)
                valid_rows.append(entry)
            except StopIteration:
                # Normales Ende des Generators erreicht
                break
            except DataValidationError as e:
                logger.warning(f"Zeile übersprungen: {e}")
                continue

        if not valid_rows:
            raise DataValidationError("Datenbeschaffung fehlgeschlagen: Es konnten keine gültigen Daten extrahiert werden.")

        # Konvertierung in ein DataFrame für die nachfolgende Transformation
        return pd.DataFrame(valid_rows)
    
    def __repr__(self) -> str:
        return f"DataLoader(file='{self.file_path.name}')"