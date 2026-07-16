"""
TwinCAT 3 ADS GUI
Grafische Oberfläche zum Lesen und Schreiben der SPS-Variablen
der Benutzerverwaltung. Läuft lokal auf dem IPC.
"""

import tkinter as tk
from tkinter import ttk

import pyads

import comtypes
from comtypes import GUID, COMMETHOD, IUnknown
from ctypes import windll
from ctypes.wintypes import HWND, HRESULT

AMS_NET_ID = "192.168.244.20.1.1"
ADS_PORT   = pyads.PORT_TC3PLC1  # 851

VAR_KEY         = "gv_Benutzerverwaltung.Key"
VAR_BESCHREIBEN = "gv_Benutzerverwaltung.Beschreiben"
VAR_SCHREIBEN   = "gv_Benutzerverwaltung.Schreiben"

# Standard-TwinCAT-STRING-Größe (80 Zeichen); anpassen falls Key/Beschreiben
# als STRING(n) mit anderer Länge deklariert sind.
MAX_STRING_LEN = 80

# ── Windows-Bildschirmtastatur (Touch-Bedienung ohne physische Tastatur) ──────
# TabTip.exe direkt per subprocess zu starten öffnet die Tastatur unter
# Windows 10 zuverlässig NICHT – Windows blendet sie nur ein, wenn sie über
# die COM-Schnittstelle ITipInvocation angestoßen wird (undokumentiert, aber
# stabil, seit Windows 8 in Gebrauch).
_user32 = windll.user32

_CLSID_UIHostNoLaunch = GUID("{4CE576FA-83DC-4F88-951C-9D0782B4E376}")


class _ITipInvocation(IUnknown):
    _iid_ = GUID("{37c994e7-432b-4834-a2f7-dce1f13b834b}")
    _methods_ = [
        COMMETHOD([], HRESULT, "Toggle", (["in"], HWND, "hwnd")),
    ]


def _touch_keyboard_visible():
    return _user32.FindWindowW("IPTip_Main_Window", None) != 0


def open_touch_keyboard():
    """Öffnet die Windows-Bildschirmtastatur, falls sie nicht schon sichtbar ist."""
    if _touch_keyboard_visible():
        return
    try:
        comtypes.CoInitialize()
        obj = comtypes.CoCreateInstance(
            _CLSID_UIHostNoLaunch,
            interface=_ITipInvocation,
            clsctx=comtypes.CLSCTX_LOCAL_SERVER,
        )
        obj.Toggle(_user32.GetForegroundWindow())
    except Exception:
        pass  # keine Bildschirmtastatur verfügbar – Feld bleibt trotzdem nutzbar


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TwinCAT – Benutzerverwaltung")
        self.resizable(False, False)

        self.plc = pyads.Connection(AMS_NET_ID, ADS_PORT)
        self.connected = False
        self._writing = False

        self._build_widgets()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._connect()
        self.after(1000, self._refresh)

    def _build_widgets(self):
        self.status_var = tk.StringVar(value="Verbinde...")
        self.status_label = ttk.Label(self, textvariable=self.status_var)
        self.status_label.pack(fill="x", padx=10, pady=(10, 4))

        input_frame = ttk.LabelFrame(self, text="Werte schreiben")
        input_frame.pack(fill="x", padx=10, pady=4)
        input_frame.columnconfigure(1, weight=1)

        self.key_var = tk.StringVar()
        self.beschreiben_var = tk.StringVar()

        ttk.Label(input_frame, text="Key:").grid(
            row=0, column=0, sticky="w", padx=4, pady=4
        )
        key_entry = ttk.Entry(input_frame, textvariable=self.key_var)
        key_entry.grid(row=0, column=1, sticky="ew", padx=4, pady=4)
        key_entry.bind("<FocusIn>", lambda event: open_touch_keyboard())

        ttk.Label(input_frame, text="Beschreiben:").grid(
            row=1, column=0, sticky="w", padx=4, pady=4
        )
        beschreiben_entry = ttk.Entry(input_frame, textvariable=self.beschreiben_var)
        beschreiben_entry.grid(row=1, column=1, sticky="ew", padx=4, pady=4)
        beschreiben_entry.bind("<FocusIn>", lambda event: open_touch_keyboard())

        self.submit_btn = ttk.Button(
            input_frame, text="Übernehmen", command=self._on_submit
        )
        self.submit_btn.grid(
            row=2, column=0, columnspan=2, sticky="ew", padx=4, pady=(8, 4)
        )

        self.write_btn = ttk.Button(input_frame, text="Schreiben (gedrückt halten)")
        self.write_btn.grid(
            row=3, column=0, columnspan=2, sticky="ew", padx=4, pady=(4, 4)
        )
        self.write_btn.bind("<ButtonPress-1>", self._on_press)
        self.write_btn.bind("<ButtonRelease-1>", self._on_release)

        live_frame = ttk.LabelFrame(self, text="Aktueller SPS-Status")
        live_frame.pack(fill="x", padx=10, pady=4)
        live_frame.columnconfigure(1, weight=1)

        self.live_key_var = tk.StringVar(value="–")
        self.live_beschreiben_var = tk.StringVar(value="–")
        self.live_schreiben_var = tk.StringVar(value="–")

        ttk.Label(live_frame, text="Key:").grid(
            row=0, column=0, sticky="w", padx=4, pady=2
        )
        ttk.Label(live_frame, textvariable=self.live_key_var).grid(
            row=0, column=1, sticky="w", padx=4, pady=2
        )
        ttk.Label(live_frame, text="Beschreiben:").grid(
            row=1, column=0, sticky="w", padx=4, pady=2
        )
        ttk.Label(live_frame, textvariable=self.live_beschreiben_var).grid(
            row=1, column=1, sticky="w", padx=4, pady=2
        )
        ttk.Label(live_frame, text="Schreiben:").grid(
            row=2, column=0, sticky="w", padx=4, pady=(2, 8)
        )
        ttk.Label(live_frame, textvariable=self.live_schreiben_var).grid(
            row=2, column=1, sticky="w", padx=4, pady=(2, 8)
        )

    def _set_status(self, text, ok):
        self.status_var.set(text)
        self.status_label.configure(foreground="green" if ok else "red")

    def _connect(self):
        try:
            self.plc.open()
            self.plc.set_timeout(2000)
            self.connected = True
            self._set_status("Verbunden", ok=True)
        except Exception:
            self.connected = False
            self._set_status("Keine Verbindung – erneuter Versuch...", ok=False)
        state = ["!disabled"] if self.connected else ["disabled"]
        self.submit_btn.state(state)
        self.write_btn.state(state)

    def _refresh(self):
        try:
            if not self.connected:
                self._connect()
            if self.connected:
                values = self.plc.read_list_by_name(
                    [VAR_KEY, VAR_BESCHREIBEN, VAR_SCHREIBEN]
                )
                self.live_key_var.set(values[VAR_KEY])
                self.live_beschreiben_var.set(values[VAR_BESCHREIBEN])
                self.live_schreiben_var.set(
                    "Ja" if values[VAR_SCHREIBEN] else "Nein"
                )
                self._set_status("Verbunden", ok=True)
                self.submit_btn.state(["!disabled"])
                self.write_btn.state(["!disabled"])
        except Exception:
            self.connected = False
            self._set_status("Keine Verbindung – erneuter Versuch...", ok=False)
            self.submit_btn.state(["disabled"])
            self.write_btn.state(["disabled"])
        finally:
            self.after(1000, self._refresh)

    def _on_submit(self):
        key = self.key_var.get()[:MAX_STRING_LEN]
        beschreiben = self.beschreiben_var.get()[:MAX_STRING_LEN]
        try:
            self.plc.write_list_by_name({
                VAR_KEY: key,
                VAR_BESCHREIBEN: beschreiben,
            })
        except Exception:
            self.connected = False
            self._set_status("Schreibfehler – erneuter Versuch...", ok=False)

    def _on_press(self, event):
        self._writing = True
        try:
            self.plc.write_by_name(VAR_SCHREIBEN, True, pyads.PLCTYPE_BOOL)
        except Exception:
            self.connected = False
            self._set_status("Schreibfehler – erneuter Versuch...", ok=False)

    def _on_release(self, event):
        self._writing = False
        try:
            self.plc.write_by_name(VAR_SCHREIBEN, False, pyads.PLCTYPE_BOOL)
        except Exception:
            self.connected = False
            self._set_status("Schreibfehler – erneuter Versuch...", ok=False)

    def _on_close(self):
        if self._writing:
            try:
                self.plc.write_by_name(VAR_SCHREIBEN, False, pyads.PLCTYPE_BOOL)
            except Exception:
                pass
        try:
            self.plc.close()
        except Exception:
            pass
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
