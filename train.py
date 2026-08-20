"""
train.py
Zentrales Skript zum Trainieren, Evaluieren, Visualieren und Speichern des Modells und der Vorhersagen.
"""

import logging
from pathlib import Path
import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from src.data_pipeline.errors import InvalidFileFormat, DataValidationError, EmptyDatasetError
from data_pipeline.entsoe_loader import DataLoader
from src.data_pipeline.cleaning import DataCleaner
from src.ml.transform import DataTransformer
from src.ml.train_model import ModelPipeline
from src.ml.evaluate_model import ReportGenerator
from src.ml.visualization import DashboardRenderer

# Root-Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("ESG_Sentinel_Core")

def save_excel_report(output_path: Path, reports: dict) -> None:
    """Zentrale I/O-Schnittstelle: Schreibt die berechneten Reports sauber in Excel."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        for sheet_name, df in reports.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)

def save_model_artefacts(model_path: Path, model: IsolationForest, scaler_path: Path, scaler: StandardScaler) -> None:
    model_path.parent.mkdir(parents=True, exist_ok=True)
    scaler_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)

class ESGDataSentinel:
    """
    Zentraler System-Orchestrator für den gesamten ML-Prozess.
    Baut über Komposition die Datenpipeline aus den spezialisierten Unterklassen auf.
    """ 
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.input_file = self.base_dir / "data" / "raw" / "industrial_releases_of_pollutants_to_air.csv"
    
        # Zielpfade definieren
        self.model_path = self.base_dir / "models" / "model.joblib"
        self.scaler_path = self.base_dir / "models" / "scaler.joblib"
        self.report_path = self.base_dir / "outputs" / "reports" / "anomaly_report.xlsx"
        self.plot_path = self.base_dir / "outputs" / "figures"

        # --- KOMPOSITION (RAG-Architektur-Style) ---
        self.loader = DataLoader(self.input_file)
        # Die Pipeline besitzt und steuert eigenständige Komponenten-Klassen als Sub-Systeme
        self.cleaner = None
        self.transformer = None
        self.model_pipeline = None
        self.report_generator = None
        self.dashboard = None

    def execute_pipeline(self) -> None:
        """Führt die Pipeline geschützt aus und protokolliert jeden Teilschritt."""
        logger.info("=== ESG Data Sentinel ML-Pipeline gestartet ===")

        try:
            # --- PHASE 1: EXTRACTION (Generator-Streaming) ---
            logger.info("Schritt 1: Extrahiere Rohdaten über Lazy-Evaluation-Generatoren...")
            df_raw = self.loader.extract_data()
            logger.info(f"Rohdaten erfolgreich geladen. Dimensionen: {df_raw.shape}")

            # --- PHASE 2: DATA CLEANING ---
            logger.info("Schritt 2: Führe eine Filterung und Bereinigung der Datensätze durch...")
            self.cleaner = DataCleaner(df_raw)
            df_cleaned = self.cleaner.clean_data()
            logger.info(f"Daten erfolgreich bereinigt. Dimensionen: {df_cleaned.shape}")

            # --- PHASE 3: FEATURE ENGINEERING ---
            logger.info("Schritt 3: Führe Schadstoff-Klassifizierung und Feature Engineering durch...")
            self.transformer = DataTransformer(df_cleaned)
            df_transformed = self.transformer.transform_data()
            logger.info(f"Schadstoff-Klassifizierung und Feature Engineering abgeschlossen. Dimensionen: {df_transformed.shape}")

            # --- PHASE 4: MACHINE LEARNING ---
            logger.info("Schritt 4: Extrahiere numerische Matrix für den Isolation Forest...")
            self.model_pipeline = ModelPipeline(df_transformed)

            # Modell, Scaler und Testdatensatz aus train_model.py abholen
            model, scaler, _, X_test = self.model_pipeline.train_pipeline()
            # Evaluierung auf Testdaten
            logger.info("Evaluiere Modell auf Testdaten...")
            # Isolation Forest: 1 = Normal, -1 = Anomalie
            test_predictions = model.predict(X_test)
            test_scores = model.decision_function(X_test)

            # Gezielte Zuweisung der Vorhersagen und Anomaly Scores über den Index von X_test
            df_results = df_transformed.loc[X_test.index].copy()
            # Ummappen auf Standard-Binärklassifikation: 0 = Normal, 1 = Anomalie
            df_results["Is_Anomaly"] = [1 if x == -1 else 0 for x in test_predictions]
            df_results["Anomaly_Score"] = test_scores
            logger.info("Modelltraining abgeschlossen.")
            logger.info(f"Erkannte Anomalien: {df_results["Is_Anomaly"].sum()} von {len(df_results)} Datensätzen ({df_results["Is_Anomaly"].mean() * 100:.1f}%)")

            # --- PHASE 5: EXCEL-REPORTING ---
            logger.info("Schritt 5: Generiere konsolidierten Multi-Sheet Excel-Report...")
            self.report_generator = ReportGenerator(df_results)
            all_reports = self.report_generator.build_reports()
    
            # Excel-Export ausführen (Zentralisiertes I/O)
            save_excel_report(self.report_path, all_reports)
            logger.info(f"Excel-Report erfolgreich exportiert nach: \"{self.report_path}\".")

            # --- PHASE 6: VISUALIZATIONS ---
            logger.info("Schritt 6: Erzeuge explorative Analyseplots...")
            self.dashboard = DashboardRenderer(df_results)
            self.dashboard.generate_and_save_plots(self.plot_path)
            logger.info(f"Visualisierungen erfolgreich exportiert nach: \"{self.plot_path}\".")

            # --- PHASE 7: PERSISTIERUNG ---
            logger.info("Schritt 7: Speichere Modell-Artefakte...")
            save_model_artefacts(self.model_path, model, self.scaler_path, scaler)
            logger.info(f"Modell-Artefakte erfolgreich exportiert nach: \"{self.model_path}\".")

        # --- ROBUSTE FEHLERBEHANDLUNG ---
        except InvalidFileFormat as e:
            logger.error(f"Pipeline-Abbruch: Ungültiges Dateiformat erkannt -> {e}")
        except EmptyDatasetError as e:
            logger.error(f"Pipeline-Abbruch: Keine Daten nach der Filterung übrig -> {e}")
        except DataValidationError as e:
            logger.error(f"Pipeline-Abbruch: Validierungsfehler im Datenstrom -> {e}")
        except Exception as e:
            logger.critical(f"Unerwarteter Systemfehler: {e}", exc_info=True)

if __name__ == "__main__":
    sentinel = ESGDataSentinel()
    sentinel.execute_pipeline()