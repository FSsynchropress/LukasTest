"""
TwinCAT 3 ADS Client
Liest und schreibt SPS-Variablen über das ADS-Protokoll.

Voraussetzungen:
  - TwinCAT ADS-Route vom IPC zu diesem PC eingerichtet
  - pyads installiert: pip install pyads
"""

import pyads
from pyads import Connection

# ── Konfiguration ────────────────────────────────────────────────────────────

# AMS Net ID des TwinCAT-IPCs (Format: x.x.x.x.1.1)
IPC_AMS_NET_ID = "192.168.1.10.1.1"

# ADS-Port der SPS-Laufzeit (851 = TwinCAT 3 erste Runtime)
ADS_PORT = pyads.PORT_TC3PLC1  # 851

# Lokale AMS Net ID dieses PCs (muss in TwinCAT als Route eingetragen sein)
# Leer lassen wenn pyads diese automatisch erkennen soll
LOCAL_AMS_NET_ID = ""


# ── Verbindung ────────────────────────────────────────────────────────────────

def connect() -> Connection:
    """Öffnet eine ADS-Verbindung zur TwinCAT-Runtime."""
    if LOCAL_AMS_NET_ID:
        pyads.open_port()
        pyads.set_local_address(LOCAL_AMS_NET_ID)

    plc = pyads.Connection(IPC_AMS_NET_ID, ADS_PORT)
    plc.open()
    print(f"Verbunden mit {IPC_AMS_NET_ID}:{ADS_PORT}")
    return plc


# ── Lesen ─────────────────────────────────────────────────────────────────────

def read_variable(plc: Connection, name: str, plc_type: type):
    """
    Liest eine einzelne SPS-Variable.

    Args:
        plc:      Offene ADS-Verbindung
        name:     Vollständiger Variablenname, z.B. 'MAIN.bEnable'
        plc_type: pyads-Typ, z.B. pyads.PLCTYPE_BOOL, PLCTYPE_INT, PLCTYPE_REAL

    Returns:
        Aktueller Wert der Variable
    """
    value = plc.read_by_name(name, plc_type)
    print(f"  {name} = {value}")
    return value


def read_multiple(plc: Connection, variables: dict) -> dict:
    """
    Liest mehrere Variablen in einem einzelnen ADS-Request (Sum-Command).

    Args:
        plc:       Offene ADS-Verbindung
        variables: Dict {variablenname: pyads_typ}

    Returns:
        Dict {variablenname: wert}
    """
    handles = plc.get_handle_list(list(variables.keys()))
    values = plc.read_list_by_handle(
        {h: t for h, t in zip(handles, variables.values())}
    )
    result = dict(zip(variables.keys(), values))
    for name, value in result.items():
        print(f"  {name} = {value}")
    plc.release_handle_list(handles)
    return result


# ── Schreiben ─────────────────────────────────────────────────────────────────

def write_variable(plc: Connection, name: str, value, plc_type: type):
    """
    Schreibt einen Wert in eine SPS-Variable.

    Args:
        plc:      Offene ADS-Verbindung
        name:     Vollständiger Variablenname
        value:    Zu schreibender Wert
        plc_type: pyads-Typ der Variable
    """
    plc.write_by_name(name, value, plc_type)
    print(f"  {name} <- {value}")


# ── Notification (zyklische Benachrichtigung) ─────────────────────────────────

def setup_notification(plc: Connection, name: str, plc_type: type, callback):
    """
    Registriert eine Benachrichtigung die bei Wertänderung ausgelöst wird.

    Args:
        plc:      Offene ADS-Verbindung
        name:     Vollständiger Variablenname
        plc_type: pyads-Typ der Variable
        callback: Funktion(handle, name, timestamp, value) die aufgerufen wird

    Returns:
        notification_handle (zum späteren Abmelden)
    """
    attr = pyads.NotificationAttrib(
        length=pyads.size_of_plc_type(plc_type),
        trans_mode=pyads.ADSTRANS_SERVERONCHA,   # nur bei Wertänderung
        max_delay=0,
        cycle_time=0,
    )
    handle, _ = plc.add_device_notification(name, attr, callback)
    print(f"  Notification registriert für '{name}' (handle={handle})")
    return handle


def remove_notification(plc: Connection, handle: int):
    plc.del_device_notification(handle)


# ── Beispiel-Nutzung ──────────────────────────────────────────────────────────

def example_callback(notification, name):
    """Wird bei jeder Wertänderung der überwachten Variable aufgerufen."""
    handle, timestamp, value = notification
    print(f"  [{timestamp}] {name} geändert: {value}")


def main():
    plc = connect()
    try:
        print("\n--- Einzelne Variablen lesen ---")
        read_variable(plc, "MAIN.bEnable",     pyads.PLCTYPE_BOOL)
        read_variable(plc, "MAIN.nCounter",    pyads.PLCTYPE_INT)
        read_variable(plc, "MAIN.fTemperatur", pyads.PLCTYPE_REAL)

        print("\n--- Mehrere Variablen lesen (Sum-Command) ---")
        read_multiple(plc, {
            "MAIN.bEnable":     pyads.PLCTYPE_BOOL,
            "MAIN.nCounter":    pyads.PLCTYPE_INT,
            "MAIN.fTemperatur": pyads.PLCTYPE_REAL,
        })

        print("\n--- Variable schreiben ---")
        write_variable(plc, "MAIN.bEnable", True, pyads.PLCTYPE_BOOL)

        print("\n--- Notification einrichten ---")
        handle = setup_notification(
            plc, "MAIN.nCounter", pyads.PLCTYPE_INT, example_callback
        )

        print("Warte 10 Sekunden auf Änderungen … (Ctrl+C zum Abbrechen)")
        import time
        time.sleep(10)

        remove_notification(plc, handle)

    finally:
        plc.close()
        print("\nVerbindung getrennt.")


if __name__ == "__main__":
    main()
