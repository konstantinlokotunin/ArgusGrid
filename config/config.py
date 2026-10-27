"""
config.py
Zentrales Konfigurationsmodul für ArgusGrid.
"""

import os
from pathlib import Path

# Speicherorte: ausgehend von dieser Datei den Projektordner finden.
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# Stromgebiete: kurze EIC (Energy Identification Codes) der ENTSO-E Datenquelle zuordnen.
MARKET_AREAS = {
    # DACH-Region & Kernmärkte
    "DE-LU": "10Y1001A1001A82H",  # Deutschland-Luxemburg (Bidding Zone)
    "DE-AT-LU": "10Y1001A1001A63L", # Ehemalige gemeinsame Zone (historische Daten)
    "AT": "10YAT-APG------L",     # Österreich (Austrian Power Grid)
    "CH": "10YCH-SWISSGRIDZ",     # Schweiz
    "NL": "10YNL----------L",     # Niederlande
    "FR": "10YFR-RTE------C",     # Frankreich
    "BE": "10YBE----------2",     # Belgien

    # Nordics (Skandinavien)
    "DK1": "10YDK-1--------W",    # Dänemark West (Jütland/Fünen)
    "DK2": "10YDK-2--------M",    # Dänemark Ost (Seeland)
    "NO1": "10YNO-1--------2",    # Norwegen Süd-Ost
    "NO2": "10YNO-2--------V",    # Norwegen Süd-West
    "NO3": "10YNO-3--------G",    # Norwegen Mitte
    "NO4": "10YNO-4--------8",    # Norwegen Nord
    "NO5": "10YNO-5--------E",    # Norwegen West
    "SE1": "10YDOM-SE-1----K",    # Schweden Nord (Luleå)
    "SE2": "10YDOM-SE-2----E",    # Schweden Mitte-Nord (Sundsvall)
    "SE3": "10YDOM-SE-3----8",    # Schweden Mitte-Süd (Stockholm)
    "SE4": "10YDOM-SE-4----2",    # Schweden Süd (Malmö)
    "FI": "10YFI-1--------U",     # Finnland

    # Osteuropa & Baltikum
    "PL": "10YPL-AREA-----S",     # Polen
    "CZ": "10YCZ-CEPS-----N",     # Tschechien
    "SK": "10YSK-SEPS-----K",     # Slowakei
    "HU": "10YHU-MAVIR----U",     # Ungarn
    "RO": "10YRO-TEL------P",     # Rumänien
    "BG": "10YCA-BULGARIA-R",     # Bulgarien
    "EE": "10Y1001A1001A39I",     # Estland
    "LV": "10YLV-1001A00074",     # Lettland
    "LT": "10YLT-1001A0008Q",     # Litauen

    # West- & Südeuropa
    "GB": "10YGB----------A",     # Großbritannien
    "IE": "10YIE-1001A00010",     # Irland (SEM)
    "ES": "10YES-REE------0",     # Spanien
    "PT": "10YPT-REN------W",     # Portugal
    "IT-North": "10Y1001A1001A81J", # Italien Nord
    "IT-Center-North": "10Y1001A1001A70O", # Italien Mittel-Nord
    "IT-Center-South": "10Y1001A1001A71M", # Italien Mittel-Süd
    "IT-South": "10Y1001A1001A788", # Italien Süd
    "GR": "10YGR-HTSO-----Y",     # Griechenland
}

# Zugangsschlüssel aus der Umgebung lesen, nicht im Code speichern.
ENTSOE_API_TOKEN = os.environ.get("ENTSOE_API_TOKEN", "d0168f23-7637-489f-9333-9471a58cd8ef").strip()