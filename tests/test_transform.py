"""
test_transform.py
Automatisierte Unittests für die Feature-Engineering-Logik.
WICHTIG: Datei direkt im Terminal/Interpreter ausführen: python -m tests.test_transform
"""

import unittest
import numpy as np
import pandas as pd
from src.ml.transform import DataTransformer, add_features

class TestDataTransform(unittest.TestCase):
    """Testsuite für die Validierung der reinen Transformationsfunktionen und OOP-Klassen."""

    def setUp(self):
        """Erstellt ein minimales, kontrolliertes Test-DataFrame."""
        self.mock_data = pd.DataFrame({
            "Country": ["Austria", "Austria"],
            "Year": ["2024", "2023"],
            "Code": ["4", "4"],
            "Sector": ["Chemical industry", "Chemical industry"],
            "Facility": ["Sample Facility GmbH", "Sample Facility GmbH"],
            "Pollutant": ["Hydrochlorofluorocarbons (HCFCs)", "Hydrochlorofluorocarbons (HCFCs)"],
            "Amount": [100.0, -134.0] # Zeile enthält einen fehlerhaften negativen Wert
        })

    def test_add_features_function(self):
        """Prüft, ob die reine Funktion add_features aus dem transform.py Modul die Basis-Features und Flags korrekt berechnet."""
        # Aufruf der reinen Funktion
        df_result = add_features(self.mock_data)

        # 1. Schadstoffgruppen-Mapping prüfen (Zeile 1, Index 1)
        self.assertEqual(df_result.loc[1, "Pollutant_Group"], "Regulated Climate/Ozone Risk")

        # 2. Mathematischen Guardrail (Is_Negative-Flag) prüfen
        self.assertFalse(df_result.loc[0, "Is_Negative"])
        self.assertTrue(df_result.loc[1, "Is_Negative"])

        # 3. Log-Transformation absichern (darf bei -134.0 nicht crashen, da vorher auf 0 geclippt)
        self.assertEqual(df_result.loc[1, "Amount_Log"], np.log1p(0.0))

    def test_data_transformer_oop_component(self):
        """Prüft, ob die OOP-Komponente alle Features sequentiell ohne Fehler berechnet."""
        transformer = DataTransformer(self.mock_data)
        df_result = transformer.transform_data()

        # Prüfen, ob alle erwarteten Feature-Spalten erzeugt wurden
        expected_columns = [
            "Amount_Log", "Dev_from_Group_Median", 
            "Dev_from_Sector_Median", "Dev_from_Sector_Group_Median", 
            "YoY_Change_Pct"
        ]
        for col in expected_columns:
            self.assertIn(col, df_result.columns)

if __name__ == "__main__":
    unittest.main()