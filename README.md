# ArgusGrid – Datenqualitätsprüfung für Energiedaten

Stand: 28.09.2026 · Arbeitsstand 1: Datenzugriff und überprüfbare Datengrundlage.

Dieses Paket entwickelt die fünf hochgeladenen ArgusGrid-Module weiter. Es enthält
eine ausführbare Datenpipeline mit Rohdatenarchiv, Qualitätsflags, Testfällen und
einem Fahrplan zum TensorFlow-Autoencoder und Streamlit-Frontend. Modelltraining
und Oberfläche sind in diesem Arbeitsstand noch nicht implementiert.

Die Loader ersetzen die bisherigen gleichnamigen Dateien. Bitte zunächst das
gesamte Paket in einen eigenen Projektordner entpacken: Die Loader verwenden die
mitgelieferten neuen Module `cleaning.py`, `http.py` und `storage.py`.

## In Windows PowerShell starten

Voraussetzung: Python 3.12, 64 Bit. Im entpackten Ordner `argusgrid`:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

Das direkte Aufrufen des Python-Interpreters in `.venv` benötigt keine Änderung
der PowerShell-Ausführungsrichtlinie. In VS Code denselben Interpreter auswählen.
Die Versionsangaben betreffen die hier getestete Datenpipeline. Für die spätere
TensorFlow-Phase werden kompatible ML-Versionen gemeinsam festgelegt und getestet.

## Kleiner Gasabruf ohne API-Key

Zuerst den Katalog ansehen:

```powershell
.\.venv\Scripts\python.exe discover_gas_points.py --label Baumgarten
```

Der folgende historische Smoke-Test war in dieser Prüfung erfolgreich:

```powershell
.\.venv\Scripts\python.exe run_pipeline.py --source entsog --start 2024-01-01 --end 2024-01-02 --operator-key AT-TSO-0001 --point-key ITP-00062
```

`--end` ist exklusiv; beide CLI-Grenzen beziehen sich auf UTC. Der Lauf speichert
24 Stundenwerte für den genannten Testtag. Die Verfügbarkeit anderer Zeiträume
oder Punkte ist damit nicht nachgewiesen. Eine frühere Probe mit identischen
`from`-/`to`-Datumsgrenzen lieferte HTTP 404; die überarbeitete Abfrage verwendet
eine weiter gefasste Quellabfrage plus exakte Filterung im Ergebnis.

Bei ENTSOG bezeichnet „Entry“ den Eingang aus Sicht des jeweiligen Betreibers.
Das ist nicht ohne weitere Prüfung identisch mit einem nationalen Nettoimport.

## Kleiner Stromabruf

Der zuvor im Code enthaltene Schlüssel wurde entfernt. Diesen alten Schlüssel
ersetzen/rotieren und einen neuen nur in der lokalen Umgebung setzen.
Das folgende Beispiel fragt den Wert verdeckt ab und vermeidet einen literal
eingetippten Schlüssel in der PowerShell-Befehlshistorie:

```powershell
$argusCredential = Get-Credential -UserName ENTSOE -Message 'Neuen ENTSO-E-Token als Passwort eingeben'
$env:ENTSOE_API_TOKEN = $argusCredential.GetNetworkCredential().Password
.\.venv\Scripts\python.exe run_pipeline.py --source entsoe --start 2024-01-01 --end 2024-01-03 --area AT
Remove-Item Env:ENTSOE_API_TOKEN
Remove-Variable argusCredential
```

Der Strom-Liveabruf wurde hier nicht ausgeführt. Tests verwenden einen injizierten
Client und prüfen unter anderem UTC, Sommerzeitwechsel, NaN-Zeilen und Fehlerpfade.

## Ergebnisse finden

| Pfad | Inhalt |
|---|---|
| `data/raw/entsoe` und `data/raw/entsog` | Originale HTTP-Antwortkörper plus SHA-256, Abrufzeit und Quelle |
| `data/processed/<run_id>/<source>/part_*.csv` | Normalisierte Daten je Zeitfenster |
| `data/processed/<run_id>/<source>/part_*_quality.csv` | Zeilen mit Qualitätskennzeichen |
| `data/processed/<run_id>/run_summary.json` | Erfolg/Fehler pro Quelle, Teilresultate, Rohdatenvolumen |
| `evidence/entsog_smoke` | Tatsächlich gemessener historischer ENTSOG-Smoke-Test |
| `docs/PROJEKTREVIEW_UND_FAHRPLAN.md` | Befunde, fachliche Grenzen, offene Anforderungen und Zeitplan |
| `docs/LERNLEITFADEN_01.md` | Erläuterungen und Übungen zur ersten Implementierungsstufe |

Fehler liefern einen Exit-Code ungleich null. Bei `--source both` wird die zweite
Quelle auch bei einem Fehler der ersten versucht; ein Teilerfolg bleibt im
Gesamtstatus ein fehlgeschlagener Lauf. Teilresultate werden explizit dokumentiert.

Für größere Abrufe verwendet der Orchestrator `iter_frames()` und speichert jeden
Block sofort. `extract_data()` lädt absichtlich den gesamten gewählten Zeitraum
in den Arbeitsspeicher und ist nur für kleine interaktive Abfragen vorgesehen.

```powershell
.\.venv\Scripts\python.exe check_data_volume.py
```

Dieser Befehl verifiziert Hashes und berichtet Bytes, MB und MiB je Quelle. Er
liefert Exit-Code 1, solange nicht beide Quellen mindestens 30.000.000 Rohbytes
erreichen. Das ersetzt weder den Bewertungsbogen noch die Prüfung, ob echte,
inhaltlich geeignete und nicht überlappende Beobachtungen vorliegen. Die Testdaten
im Paket erfüllen diese Größenanforderung ausdrücklich noch nicht.

## Noch offene Grenzen

- Die Zeilenflags prüfen vorhandene Zeilen. Eine vollständige Zeitrasterprüfung
  auf ausgebliebene Zeitpunkte und nicht gemeldete Produktionsarten folgt separat.
- `not_applicable` ist ein Quellhinweis, kein automatisch bestätigter Datenfehler.
  Negative Werte werden ohne quellspezifische Regel nicht pauschal verworfen.
- Gasreihen bleiben anhand Betreiber, Punkt, Richtung, Indikator, Einheit,
  Periodentyp und Dataset getrennt. Revisionsauswahl ist noch festzulegen.
- Stromspalten enthalten Produktionsart und gegebenenfalls Generation/Consumption.
  Die Differenzierung wird bewahrt; es findet keine unbegründete Nettierung statt.
- Rohantworten werden nach Inhalt dedupliziert. Gas-Abfragepuffer, Revisionen und
  andere Überlappungen können dennoch gleiche fachliche Beobachtungen enthalten.
- Ein leeres Zeitfenster bricht den jeweiligen Quellenlauf sichtbar ab. Automatische
  Wiederaufnahme und eine separate Abdeckungstabelle sind nächste Ausbauschritte.
- Höhere Modell-Scores werden später als Prüfhinweise bezeichnet. Der Code erzeugt
  noch keine ML-Scores und stellt keine Feststellung eines Meldefehlers dar.

Der offizielle Projektauftrag/Bewertungsbogen fehlt. Daher gibt es noch keine
vollständige Anforderungsfreigabe und keine Zusage einer bestimmten Benotung.
