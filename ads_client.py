"""
TwinCAT 3 ADS Client
Liest und schreibt SPS-Variablen über das ADS-Protokoll.
Läuft lokal auf dem IPC (192.168.244.20.1.1).
"""

import pyads

AMS_NET_ID = "192.168.244.20.1.1"
ADS_PORT   = pyads.PORT_TC3PLC1  # 851


def main():
    plc = pyads.Connection(AMS_NET_ID, ADS_PORT)
    plc.open()
    print(f"Verbunden mit {AMS_NET_ID}")

    try:
        # ── Lesen ──────────────────────────────────────────────────────────
        schreiben = plc.read_by_name("gv_Benutzerverwaltung.Schreiben", pyads.PLCTYPE_BOOL)
        key = plc.read_by_name("gv_Benutzerverwaltung.Key", pyads.PLCTYPE_STRING)
        beschreiben = plc.read_by_name("gv_Benutzerverwaltung.Beschreiben", pyads.PLCTYPE_STRING)
        print(f"gv_Benutzerverwaltung.Schreiben = {schreiben}")
        print(f"gv_Benutzerverwaltung.Key = {key}")
        print(f"gv_Benutzerverwaltung.Beschreiben = {beschreiben}")

        # ── Schreiben (Beispiel) ────────────────────────────────────────────
        # plc.write_by_name("gv_Benutzerverwaltung.Schreiben", True, pyads.PLCTYPE_BOOL)

    finally:
        plc.close()
        print("Verbindung getrennt.")


if __name__ == "__main__":
    main()
