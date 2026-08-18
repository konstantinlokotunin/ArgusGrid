"""predict.py
Separat ausführbares Skript zur Inferenz (Vorhersage).
Lädt das trainierte Modell und wendet es auf neue Daten an (Anforderung 8).
"""

import logging
from pathlib import Path
import joblib
import pandas as pd

# Root-Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("ESG_Sentinel_Core")

def predict_new_sample(sample: dict) -> None:
    """Lädt die gespeicherten Artefakte und erstellt eine neue Vorhersage."""
    base_dir = Path(__file__).parent
    model_path = base_dir / "models" / "model.joblib"
    scaler_path = base_dir / "models" / "scaler.joblib"

    if not model_path.exists() or not scaler_path.exists():
        raise FileNotFoundError("Modell-Artefakte nicht gefunden! Bitte train.py zuerst ausführen.")
    
    # Gespeicherte Modell-Artefakte laden
    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)

    # Eingabedaten in DataFrame umwandeln
    df_new = pd.DataFrame([sample])

    # Features exakt wie im Training anordnen
    feature_cols = [
        "Amount_Log",
        "Dev_from_Group_Median",
        "Dev_from_Sector_Median",
        "Dev_from_Sector_Group_Median",
        "YoY_Change_Pct",
    ]

    # Features skalieren
    df_scaled = scaler.transform(df_new[feature_cols])

    # Vorhersage treffen
    prediction = model.predict(df_scaled)
    score = model.decision_function(df_scaled)

    # Ergebnis bestimmen
    status = "ANOMALIE (Erhöhtes Risiko von Schadstoffemissionen)" if prediction[0] == -1 else "KEIN ANOMALER WERT"
    
    # Da dies ein Standalone-Anwenderskript außerhalb der Pipeline ist,
    # wird das Ergebnis der Vorhersage hier für den Endnutzer ausgeben.
    print("\n" + "="*40)
    print("🔮 ESG DATA SENTINEL - NEUE VORHERSAGE")
    print("="*40)
    print(f"Ergebnis:      {status}")
    print(f"Anomaly-Score: {score[0]:.4f}")
    print("="*40)
    

if __name__ == "__main__":
    # Beispiel für einen neuen, simulierten Schadstoff-Datensatz (Inferenz-Eingabe)
    sample = {
        "Country": "Austria",
        "Year": "2016",
        "Code": "4",
        "Sector": "Chemical industry",
        "Facility": "Sample Facility GmbH",
        "Pollutant": "Hydrochlorofluorocarbons (HCFCs)",
        "Amount": 208,
        "Pollutant_Group": "Regulated Climate/Ozone Risk",
        "Is_Negative": False,
        "Amount_Log": 5.3,
        "Dev_from_Group_Median": 4.2,
        "Dev_from_Sector_Median": 3.8,
        "Dev_from_Sector_Group_Median": 5.1,
        "YoY_Change_Pct": 75.0  # Massiver Anstieg im Jahresvergleich!
        }
    
    predict_new_sample(sample)