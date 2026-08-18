"""
visualization.py
Kapselt die Generierung von Kontrollplots für die Bonus-Anforderungen.
Trennt die reine Plot-Erstellung strikt von den Datei-Schreiboperationen (I/O).
"""

from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import pandas as pd
import seaborn as sns

# ==========================================
# REINE FUNKTIONEN
# ==========================================

def style_ax(ax, title: str, xlabel: str | None, ylabel: str | None) -> None:
    """
    Styling-Schnittstelle für ein konsistentes, professionelles Layout.
    """
    sns.despine(ax=ax, left=False, bottom=False)
    for spine in ["left", "bottom", "right", "top"]:
        ax.spines[spine].set_linewidth(1.1)
        ax.spines[spine].set_color("#9ca3af")

    ax.set_facecolor("#F7FBFF") # Konsistenter, leicht bläulicher Hintergrund
    ax.grid(axis="y", linestyle="--", alpha=0.5, color="#ccc")
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=13, labelpad=8, color="#222222")
    else:
        ax.set_xlabel(None)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=13, labelpad=8, color="#222222")
    else:
        ax.set_ylabel(None)
    ax.set_title(title, fontsize=15, weight="bold", pad=15, color="#222222")

def plot_anomaly_distribution(df: pd.DataFrame) -> Figure:
    """
    Erstellt den Plot für die Verteilung der Anomaly Scores.
    Niedrigere Werte für den Anomaly Score deuten auf ungewöhnlichere Datensätze hin.
    """
    fig, ax = plt.subplots(figsize=(12, 6))
    style_ax(ax, title="Distribution of Anomaly Scores", xlabel="Anomaly Score", ylabel="Number of Records")
    ax.set_xlabel("Anomaly Score", fontsize=12)

    sns.histplot(data=df, x="Anomaly_Score", bins=40, color="#1a73e8", edgecolor="white", alpha=0.85, ax=ax)
    ax.axvline(x=0, color="#DB3A34", linestyle="--", linewidth=2, label="Decision threshold")
    ax.legend(loc="best", frameon=False)
    
    return fig

def plot_sector_anomalies(df: pd.DataFrame) -> Figure:
    """Reine Funktion: Erstellt das Balkendiagramm der Anomalien nach Sektor."""
    anomalies = df[df["Is_Anomaly"] == 1]
    sector_counts = anomalies.groupby("Sector").size().sort_values(ascending=False).reset_index(name="Count")

    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(data=sector_counts, x="Sector", y="Count", color="#1a73e8", alpha=0.85, ax=ax)
    style_ax(ax, title="Sectors by Anomaly Count", xlabel= None, ylabel="Number of Anomalies")
    ax.tick_params(axis='x', rotation=20)
    ax.set_ylim(0, ax.get_ylim()[1] * 1.05)

    # Prozentuale Labels hinzufügen
    total = len(anomalies)
    for bar in ax.patches:
        height = int(bar.get_height())
        pct = (height / total) * 100 if total > 0 else 0
        ax.text(bar.get_x() + bar.get_width()/2, height + 0.25, f"{height}\n({pct:.1f}%)", ha="center", va="bottom", fontsize=9)
    
    return fig

def plot_group_anomalies(df: pd.DataFrame) -> Figure:
    """Reine Funktion: Erstellt das Balkendiagramm der Anomalien nach Schadstoffgruppe."""
    anomalies = df[df["Is_Anomaly"] == 1]
    group_counts = anomalies.groupby("Pollutant_Group").size().sort_values(ascending=False).reset_index(name="Count")

    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(data=group_counts, x="Pollutant_Group", y="Count", color="#1a73e8", alpha=0.85, ax=ax)
    style_ax(ax, title="Anomalies by Pollutant_Group", xlabel= None, ylabel="Number of Anomalies")
    ax.tick_params(axis='x', rotation=20)
    ax.set_ylim(0, ax.get_ylim()[1] * 1.05)

    # Prozentuale Labels hinzufügen
    total = len(anomalies)
    for bar in ax.patches:
        height = int(bar.get_height())
        pct = (height / total) * 100 if total > 0 else 0
        ax.text(bar.get_x() + bar.get_width()/2, height + 0.25, f"{height}\n({pct:.1f}%)", ha="center", va="bottom", fontsize=9)
    
    return fig

def plot_heatmap_matrix(df: pd.DataFrame) -> Figure:
    """Reine Funktion: Erstellt eine Heatmap für Sektoren und Schadstoffgruppen."""
    anomalies = df[df["Is_Anomaly"] == 1].copy()
    heatmap_data = pd.crosstab(anomalies["Sector"], anomalies["Pollutant_Group"])

    fig, ax = plt.subplots(figsize=(12, 6))
    sns.heatmap(heatmap_data, annot=True, fmt=".0f", cmap="Blues", linewidths=1.2, linecolor="#D2D3DB", cbar=True, square=True, ax=ax)
    style_ax(ax, title="Anomalies by Sector and Pollutant Group", xlabel=None, ylabel=None)
    ax.tick_params(axis='x', rotation=20)
    
    return fig

# ==========================================
# OOP-KOMPONENTE
# ==========================================

class DashboardRenderer:
    """Komponente zur Steuerung und Speicherung der Grafiken."""
    
    def __init__(self, df_results: pd.DataFrame):
        self.df_results = df_results

    def generate_and_save_plots(self, output_dir: Path) -> None:
        """I/O-Schnittstelle: Ruft reine Funktionen auf und speichert die Grafiken speicherschonend."""
        # Einmalig das globale Theme für diesen Run setzen
        sns.set_theme(style="white", font="sans-serif")
        output_dir.parent.mkdir(parents=True, exist_ok=True)

        # Zuordnung von Dateinamen zu den reinen Top-Level-Funktionen
        plots_to_create = {
            "anomaly_score_distribution.png": plot_anomaly_distribution,
            "sectors_by_anomaly_count.png": plot_sector_anomalies,
            "anomalies_by_pollutant_group.png": plot_group_anomalies,
            "anomalies_by_sector_and_pollutant_group.png": plot_heatmap_matrix
        }
        
        # Daten übergeben, Figure zurückbekommen
        for filename, plot in plots_to_create.items():
            fig = plot(self.df_results)
            # Speicherprozess (I/O) ausführen
            target_path = output_dir / filename
            fig.savefig(target_path, bbox_inches="tight", dpi=300)
            
            # Memory Leak Prevention
            plt.close(fig)

    def __repr__(self) -> str:
        return f"DashboardRenderer(Rows={len(self.df_results)})"