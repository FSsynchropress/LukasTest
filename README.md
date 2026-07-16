# TwinCAT 3 ADS Client

Python-Programm zum Lesen und Schreiben von SPS-Variablen über das ADS-Protokoll.

## Voraussetzungen

### Auf dem Windows-IPC (TwinCAT-Seite)
1. TwinCAT 3 Runtime läuft mit einer SPS-Applikation
2. ADS-Route vom IPC zu deinem PC eingerichtet  
   → TwinCAT System Manager → Routes → Route hinzufügen  
   → AMS Net ID des Client-PCs eintragen

### Auf dem Client-PC (dieser Code)
- Python 3.8+
- TwinCAT ADS-DLL installiert (kommt mit TwinCAT oder als separates  
  [TC1000 ADS](https://www.beckhoff.com/de-de/products/automation/twincat/tc1xxx-twincat-3-base/tc1000.html) Paket)
- ADS-Route zurück zum IPC eingetragen

## Installation

```bash
pip install -r requirements.txt
```

## Konfiguration

In `ads_client.py` die Verbindungsdaten anpassen:

```python
IPC_AMS_NET_ID = "192.168.1.10.1.1"   # AMS Net ID des IPCs
ADS_PORT = pyads.PORT_TC3PLC1          # 851 = erste Runtime
```

Die AMS Net ID des IPCs steht in TwinCAT unter:  
**System → Routes → eigene Route → AMS Net ID**

## Verwendung

```bash
python ads_client.py
```

### Variablen lesen

```python
import pyads

plc = pyads.Connection("192.168.1.10.1.1", pyads.PORT_TC3PLC1)
plc.open()

wert = plc.read_by_name("MAIN.nCounter", pyads.PLCTYPE_INT)
print(wert)

plc.close()
```

### Variablen schreiben

```python
plc.write_by_name("MAIN.bEnable", True, pyads.PLCTYPE_BOOL)
```

## GUI (Benutzerverwaltung)

Statt der Kommandozeile kann eine grafische Oberfläche verwendet werden:

```bash
python ads_gui.py
```

Sie verbindet sich beim Start automatisch, zeigt den Verbindungsstatus sowie
die aktuellen SPS-Werte von Key, Beschreiben und Schreiben an (aktualisiert
sich jede Sekunde), und bietet zwei getrennte Buttons:

- **Übernehmen** – schreibt die Eingabefelder Key/Beschreiben auf einen Klick
  in die SPS.
- **Schreiben (gedrückt halten)** – setzt `gv_Benutzerverwaltung.Schreiben`
  auf `True` solange der Button gedrückt gehalten wird, und beim Loslassen
  automatisch wieder auf `False`.

tkinter ist Teil der Standard-Python-Installation von python.org, es wird
keine zusätzliche Bibliothek benötigt. Falls beim Start ein Fehler wie
`No module named tkinter` erscheint: den Python-Installer erneut ausführen,
"Modify" wählen und sicherstellen, dass "tcl/tk and IDLE" aktiviert ist.

### Unterstützte Datentypen

| pyads-Typ            | SPS-Typ   |
|----------------------|-----------|
| `PLCTYPE_BOOL`       | BOOL      |
| `PLCTYPE_INT`        | INT       |
| `PLCTYPE_UINT`       | UINT      |
| `PLCTYPE_DINT`       | DINT      |
| `PLCTYPE_UDINT`      | UDINT     |
| `PLCTYPE_REAL`       | REAL      |
| `PLCTYPE_LREAL`      | LREAL     |
| `PLCTYPE_STRING`     | STRING    |
| `PLCTYPE_WORD`       | WORD      |
| `PLCTYPE_DWORD`      | DWORD     |

## ADS-Ports

| Port | Bedeutung                  |
|------|----------------------------|
| 851  | TC3 PLC Runtime 1          |
| 852  | TC3 PLC Runtime 2          |
| 10000| TwinCAT System Service     |
| 300  | NC Task 1 (Bewegungssteuerung) |
