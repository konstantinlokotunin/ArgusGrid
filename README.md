# ESG Data Sentinel

Ein Machine-Learning-Projekt zur Erkennung potenzieller Datenqualitätsrisiken in industriellen Emissionsdaten.

---

## 📌 Übersicht & Zielsetzung

Das Projekt identifiziert auffällige Datenpunkte (Red Flags) in öffentlich berichteten Emissionsdaten österreichischer Industrieanlagen. Es dient als Vorstufe zur ESG-Datenvalidierung, beispielsweise im Rahmen von *Limited Assurance Engagements*.

### Erkannte Anomalietypen
* **Numerische Fehler:** Negative Werte oder extreme Ausreißer.
* **Metrische Fehler:** Mögliche Skalierungs- und Einheitenfehler.
* **Temporale Fehler:** Extreme Year-over-Year-Veränderungen (Vorjahresvergleich).
* **Kontextuelle Fehler:** Sektor- oder schadstoffspezifische Abweichungen.

---

## 🤖 Machine Learning Ansatz

Da verlässliche Fehlerlabels fehlen, nutzt das Projekt ein **unüberwachtes Verfahren (Unsupervised Learning)**.

* **Algorithmus:** `IsolationForest`
* **Vorteil:** Benötigt keine gelabelten Trainingsdaten; isoliert Anomalien basierend auf numerischen Mustern.
* **Klassifikation:**
  * `1` (Normal) ➔ Unauffälliger Datenpunkt.
  * `-1` (Anomalie) ➔ Potenziell prüfungswürdiger Datenpunkt / Red Flag.

> 💡 **Methodischer Hinweis:** Fehlende Werte (*Missing Values*) werden vorab deterministisch via Pandas in der Transformationsphase bereinigt. Das ML-Modell fokussiert sich rein auf komplexe, nicht-regelbasierte Musterabweichungen.

---

## 📊 Datenbasis & Scope

Die Daten stammen aus dem **European Industrial Emissions Portal** mit folgendem Fokus:

* **Geografie:** Österreich (AT)
* **Datentyp:** Industrielle Emissionsdaten (tabellarisch)
* **Scope:** Fokus auf Datenintegrität und Qualitätssicherung

---

## 📂 Projektstruktur

Das Projekt ist strikt modular nach Schichten und Paketen organisiert, um Zirkelbezüge zu vermeiden:

```text
esg-data-sentinel/
│
├── data/                            # Reiner Datenordner
│   └── raw/                         # Unveränderte Original-CSV-Datei
│
├── outputs/                         # Zentraler Ausgabeordner für Artefakte und Berichte
│   ├── figures/                     # Von train.py erzeugte Dashboard-Plots
│   └── reports/                     # Von den Skripten erzeugte Tabellen und Berichte
│       ├── anomaly_report.xlsx      # Konsolidierter Multi-Sheet Excel-Bericht
│       └── missing_data_report.csv  # Von main.py erzeugte Übersicht fehlender Werte
│
├── models/                          # Speicherort für serialisierte ML-Objekte
│   ├── model.joblib                 # Das gespeicherte, trainierte ML-Modell
│   └── scaler.joblib                # Der gespeicherte Daten-Scaler
│
├── src/                             # Haupt-Code-Ordner
│   │
│   ├── pipeline/                    # PAKET 1: Datenbeschaffung & Bereinigung
│   │   ├── __init__.py              # Paket-Initialisierung
│   │   ├── errors.py                # Eigene Exceptions: InvalidFileFormat, DataValidationError, EmptyDatasetError
│   │   ├── extract.py               # Zeilenweiser Streaming-Generator (Lazy Loading)
│   │   └── cleaning.py              # Reine Funktionen zur Filterung & Bereinigung
│   │
│   └── ml/                          # PAKET 2: Daten-Analyse & Modellierung
│      ├── __init__.py               # Paket-Initialisierung
│      ├── transform.py              # Reine Funktionen für Schadstoff-Klassifizierung & Feature Engineering
│      ├── train_model.py            # Mathematische Pipeline für Train-Test-Splitting & Modell-Fitting
│      ├── evaluate_model.py         # Reine mathematische Metriken-Aggregation für Berichte
│      └── visualization.py          # Reine Plotting-Funktionen (Memory Leak geschützt)
│
├── tests/
│   └── test_transform.py            # Automatisierte Unittests
├── main.py                          # Reiner ETL-Orchestrator: Extraktion, Bereinigung & Feature-Export
├── train.py                         # ML-Zentrale: Trainiert, evaluiert auf Testdaten und speichert Reports, Dashboard-Plots & Modelle
├── predict.py                       # Standalone-Inferenz: Lädt Modellartefakte und klassifiziert neue Datensätze
├── requirements.txt                 # Paket-Abhängigkeiten
└── README.md                        # Projektdokumentation
```

---

## ⚡ Installation & Ausführung

### 1. Abhängigkeiten installieren
Führen Sie den folgenden Befehl in Ihrem Terminal aus, um alle benötigten Bibliotheken global oder in Ihrer Umgebung zu installieren:
```bash
pip install -r requirements.txt
```

### 2. ETL-Pipeline starten
Startet die Datenaufbereitung. Liest die Rohdaten zeilenweise ein, filtert nach Österreich, berechnet mathematische Features und speichert die vorbereiteten Daten ab.
```bash
python main.py
```

### 3. Machine-Learning-Modell trainieren, evaluieren & visualisieren
Führt den Train-Test-Split durch, trainiert den Isolation Forest, bewertet die Performance auf den Testdaten und exportiert den finalen Excel-Report sowie die Kontrollgrafiken in den Ordner `reports/`.
```bash
python train.py
```

### 4. Vorhersagen auf neuen Daten berechnen (Inferenz)
Simuliert den Produktiveinsatz. Lädt die fertigen Artefakte aus dem Ordner `models/` und klassifiziert einen neuen Datensatz sofort, ohne das Modell neu zu trainieren.
```bash
python predict.py
```
