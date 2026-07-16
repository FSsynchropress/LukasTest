"""
TwinCAT 3 ADS GUI
Grafische Oberfläche zum Lesen und Schreiben der SPS-Variablen
der Benutzerverwaltung. Läuft lokal auf dem IPC.
"""

import tkinter as tk
from tkinter import ttk

import pyads

AMS_NET_ID = "192.168.244.20.1.1"
ADS_PORT   = pyads.PORT_TC3PLC1  # 851

VAR_KEY         = "gv_Benutzerverwaltung.Key"
VAR_BESCHREIBEN = "gv_Benutzerverwaltung.Beschreiben"
VAR_SCHREIBEN   = "gv_Benutzerverwaltung.Schreiben"

# Standard-TwinCAT-STRING-Größe (80 Zeichen); anpassen falls Key/Beschreiben
# als STRING(n) mit anderer Länge deklariert sind.
MAX_STRING_LEN = 80


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
        ttk.Entry(input_frame, textvariable=self.key_var).grid(
            row=0, column=1, sticky="ew", padx=4, pady=4
        )
        ttk.Label(input_frame, text="Beschreiben:").grid(
            row=1, column=0, sticky="w", padx=4, pady=4
        )
        ttk.Entry(input_frame, textvariable=self.beschreiben_var).grid(
            row=1, column=1, sticky="ew", padx=4, pady=4
        )

        self.write_btn = ttk.Button(input_frame, text="Schreiben (gedrückt halten)")
        self.write_btn.grid(
            row=2, column=0, columnspan=2, sticky="ew", padx=4, pady=(8, 4)
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
        self.write_btn.state(["!disabled"] if self.connected else ["disabled"])

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
                self.write_btn.state(["!disabled"])
        except Exception:
            self.connected = False
            self._set_status("Keine Verbindung – erneuter Versuch...", ok=False)
            self.write_btn.state(["disabled"])
        finally:
            self.after(1000, self._refresh)

    def _on_press(self, event):
        key = self.key_var.get()[:MAX_STRING_LEN]
        beschreiben = self.beschreiben_var.get()[:MAX_STRING_LEN]
        self._writing = True
        try:
            self.plc.write_list_by_name({
                VAR_KEY: key,
                VAR_BESCHREIBEN: beschreiben,
                VAR_SCHREIBEN: True,
            })
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
