"""
app.py
Interaktives Streamlit-Dashboard für den ESG Data Sentinel.
Ermöglicht den Drag-and-Drop-Upload von ESG-Portfoliodaten.
Analyse erfolgt komplett im Hintergrund ohne Code-Sichtbarkeit für den Anwender.
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from src.pipeline.extract import DataLoader
from src.pipeline.cleaning import DataCleaner
from src.ml.transform import DataTransformer
from src.ml.train_model import ModelPipeline
import matplotlib.pyplot as plt
import seaborn as sns
import logging

@st.cache_resource
def init_logger():
    # Basis-Konfiguration für das globale Logging festlegen
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True # 'force=True' überschreibt Streamlits Standard-Formatierung
    )
    
    # 2. Spezifischen Logger für deine Core-Anwendung erstellen
    return logging.getLogger("ESG_Sentinel_Core")

# Logger initialisieren
logger = init_logger()

# 1. Page Configuration für ein professionelles Erscheinungsbild
st.set_page_config(
    page_title="ESG Data Sentinel — Audit Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Konsistentes Farb-Theme definieren (Deep Navy, ESG Green, Red-Flag Orange)
COLOR_NAVY = "#0B1B2B"
COLOR_GREEN = "#00A86B"
COLOR_RED = "#FF5A36"

# CSS-Injektion für professionelles Styling
st.markdown(f"""
    <style>
    .main-title {{ color: {COLOR_NAVY}; font-size: 38px; font-weight: bold; margin-bottom: 5px; }}
    .sub-title {{ color: "#5a6b7c"; font-size: 16px; margin-bottom: 25px; }}
    .metric-card {{ background-color: #F7FBFF; border: 1px solid #D2D3DB; border-radius: 8px; padding: 20px; text-align: center; }}
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR (Metadaten und Scope) ---
with st.sidebar:
    st.markdown("### 🛡️ Systemkonfiguration")
    st.info("Prüfmodul: Vorprüfungshandlungen im Risk Assessment (NaBeG / CSRD Portfolio-Schnittstelle)")
    st.markdown("---")
    st.markdown("**User:** ...")
    st.markdown("**Verband:** ...")
    st.markdown("**Scope:** Scope 3 — Financed Emissions Validierung")

# --- HAUPTSEITE (Titelzeile) ---
st.markdown("<div class='main-title'>ESG Data Sentinel Austria</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>Automatisierte Validierung und analytische Prüfungshandlungen für Nachhaltigkeitsdaten</div>", unsafe_allow_html=True)

st.markdown("---")

# --- FILE UPLOAD INTERFACE ---
st.markdown("### 📥 Mandanten-Datenbasis hochladen")
uploaded_file = st.file_uploader(
    "Wählen Sie die Portfolio-Emissionsdatei des Kreditinstituts aus (Format: .csv)",
    type=["csv"],
    help="Die Datei muss die standardisierten industriellen Emissionsdaten enthalten."
)

if uploaded_file is not None:
    with st.spinner("⏳ Analytische Prüfungsschritte werden ausgeführt (ETL & ML-Inferenz)..."):
        try:
            # --- PHASE 1: EXTRACTION (Generator-Streaming) ---
            logger.info("Schritt 1: Extrahiere Rohdaten...")
            df_raw = pd.read_csv(uploaded_file)
            logger.info(f"Rohdaten erfolgreich geladen.")


            # --- PHASE 2: DATA CLEANING ---
            logger.info("Schritt 2: Führe eine Filterung und Bereinigung der Datensätze durch...")
            cleaner = DataCleaner(df_raw)
            df_cleaned = cleaner.clean_data()
            logger.info(f"Daten erfolgreich bereinigt.")

            # --- PHASE 3: FEATURE ENGINEERING ---
            logger.info("Schritt 3: Führe Luftschadstoff-Klassifizierung und Feature Engineering durch...")
            transformer = DataTransformer(df_cleaned)
            df_transformed = transformer.transform_data()
            logger.info(f"Schadstoff-Klassifizierung und Feature Engineering abgeschlossen.")

            # --- PHASE 4: MACHINE LEARNING ---
            logger.info("Schritt 4: Initiere Prüfungshandlungen...")
            model_pipeline = ModelPipeline(df_transformed)
            model, _, _, X_test = model_pipeline.train_pipeline()
            # Isolation Forest: 1 = Normal, -1 = Anomalie
            test_predictions = model.predict(X_test)
            test_scores = model.decision_function(X_test)
            df_results = df_transformed.loc[X_test.index].copy()
            # Ummappen auf Standard-Binärklassifikation: 0 = Normal, 1 = Anomalie
            df_results["Is_Anomaly"] = [1 if x == -1 else 0 for x in test_predictions]
            df_results["Anomaly_Score"] = test_scores
            st.success("✅ Prüfungshandlungen erfolgreich abgeschlossen")

            # --- PHASE 5: ERGEBNIS-KPIs ---
            total_records = len(df_results)
            anomalies_count = int(df_results["Is_Anomaly"].sum())
            anomaly_rate = (anomalies_count / total_records) * 100 if total_records > 0 else 0.0
            # Drei KPI-Metriken nebeneinander platzieren
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"<div class='metric-card'><h4>Gescannte Datensätze</h4><h2 style='color:{COLOR_NAVY};'>{total_records}</h2></div>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"<div class='metric-card'><h4>Identifizierte Red Flags</h4><h2 style='color:{COLOR_RED};'>{anomalies_count}</h2></div>", unsafe_allow_html=True)
            with col3:
                st.markdown(f"<div class='metric-card'><h4>Gesamte Fehlerquote</h4><h2 style='color:{COLOR_NAVY};'>{anomaly_rate:.2f} %</h2></div>", unsafe_allow_html=True)

            st.markdown("---")

            # --- VISUALISIERUNGEN (Layout-Aufteilung) ---
            st.markdown("### 📊 Analytische Auswertungen")
            col_graph1, col_graph2 = st.columns(2)
            
            with col_graph1:
                # Plot 1: Anomalien nach Wirtschaftssektoren
                st.markdown("**Verteilung der Risiko-Kredite nach Sektoren**")
                fig, ax = plt.subplots(figsize=(7, 4))
                ax.set_facecolor("#F7FBFF")
                anomalies_df = df_results[df_results["Is_Anomaly"] == 1]
                if not anomalies_df.empty:
                    sector_counts = anomalies_df.groupby("Sector").size().sort_values(ascending=False).reset_index(name="Count")
                    sns.barplot(data=sector_counts, x="Count", y="Sector", palette="Reds_r", ax=ax)
                    ax.set_xlabel("Anzahl Red Flags")
                    ax.set_ylabel("")
                    sns.despine(ax=ax)
                    st.pyplot(fig)
                else:
                    st.info("Keine Anomalien im Datensatz vorhanden.")
                plt.close(fig)

            with col_graph2:
                # Plot 2: Verteilung der Scores
                st.markdown("**Verteilung der mathematischen Abweichungs-Scores**")
                fig, ax = plt.subplots(figsize=(7, 4))
                ax.set_facecolor("#F7FBFF")
                sns.histplot(data=df_results, x="Anomaly_Score", bins=30, color="#1a73e8", ax=ax, kde=True)
                ax.axvline(x=0, color=COLOR_RED, linestyle="--", label="Prüfschwelle")
                ax.set_xlabel("Abweichungs-Intensität (Je negativer, desto kritischer)")
                ax.set_ylabel("Anzahl")
                ax.legend(frameon=False)
                sns.despine(ax=ax)
                st.pyplot(fig)
                plt.close(fig)

            st.markdown("---")

            # --- DATA TABLE (Die konkreten Red Flags für die Prüfungsakte) ---
            st.markdown("### 📋 Zu prüfende Einzelfälle (Identifizierte Red Flags)")
            st.caption("Diese Datensätze weisen extreme methodische, temporale oder quantitative Inkonsistenzen auf und müssen im Rahmen des Substantive Testings mittels Einzelfallprüfung aufgearbeitet werden.")
            
            # Relevante Spalten für den Auditor filtern und nach Kritikalität sortieren
            df_flags = df_results[df_results["Is_Anomaly"] == 1].sort_values("Anomaly_Score", ascending=True)
            display_cols = ["Facility", "Sector", "Pollutant", "Year", "Amount", "YoY_Change_Pct", "Anomaly_Score"]
            
            st.dataframe(
                df_flags[display_cols],
                use_container_width=True,
                column_config={
                    "Amount": st.column_config.NumberColumn("Gemeldete Menge", format="%.2f"),
                    "YoY_Change_Pct": st.column_config.NumberColumn("Vorjahresabweichung (%)", format="%.1f%%"),
                    "Anomaly_Score": st.column_config.NumberColumn("Kritikalitäts-Score", format="%.4f")
                }
            )

        except Exception as e:
            st.error(f"🚨 Fehler bei der automatisierten Datenvalidierung: {str(e)}")
            st.info("Bitte überprüfen Sie, ob das Datenformat der CSRD-Schnittstellendefinition entspricht.")

else:
    # Standard-Anzeige, wenn noch keine Datei hochgeladen wurde
    st.info("🛡️ Das System ist bereit. Bitte laden Sie eine Portfolio-Emissionsdatei hoch, um die automatisierten Vorprüfungshandlungen zu starten.")