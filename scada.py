import csv
import json
import queue
import threading
import time
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk

import serial
from serial import SerialException


# =====================================================
# CONFIGURATION
# =====================================================
SERIAL_PORT = "COM10"
BAUD_RATE = 9600
WARNING_THRESHOLD = 150
CRITICAL_THRESHOLD = 250

WATCHDOG_TIMEOUT = 5
RECONNECT_INTERVAL = 3
STARTUP_GRACE_SECONDS = 3

LOG_FILE = Path(__file__).with_name("scada_history.csv")
LOG_FIELDS = [
    "timestamp", "type", "value", "state", "emergency",
    "manual_emergency", "water_emergency", "alarm_muted", "event"
]

messages = queue.Queue()
stop_event = threading.Event()


# =====================================================
# JOURNAL CSV
# =====================================================
def write_log(kind, data):
    try:
        new_file = not LOG_FILE.exists() or LOG_FILE.stat().st_size == 0

        with LOG_FILE.open("a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(
                file, fieldnames=LOG_FIELDS, extrasaction="ignore"
            )
            if new_file:
                writer.writeheader()

            writer.writerow({
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "type": kind,
                **data
            })
    except OSError as exc:
        messages.put(("log_error", str(exc)))


# =====================================================
# VALIDATION DES TELEMETRIES
# =====================================================
def validate_telemetry(data):
    if not isinstance(data, dict):
        return False, "Le JSON doit être un objet"

    if data.get("sensor") != "water_level":
        return False, "Capteur inconnu"

    value = data.get("value")
    if type(value) is not int or not 0 <= value <= 1023:
        return False, "Mesure invalide : plage 0-1023"

    if data.get("warning_threshold") != WARNING_THRESHOLD:
        return False, "Seuil avertissement incorrect"

    if data.get("critical_threshold") != CRITICAL_THRESHOLD:
        return False, "Seuil critique incorrect"

    for field in (
        "emergency", "manual_emergency",
        "water_emergency", "alarm_muted"
    ):
        if type(data.get(field)) is not bool:
            return False, f"Champ booléen invalide : {field}"

    water = data["water_emergency"]
    manual = data["manual_emergency"]

    if water != (value >= CRITICAL_THRESHOLD):
        return False, "Urgence eau incohérente"

    if data["emergency"] != (water or manual):
        return False, "Urgence générale incohérente"

    if water:
        expected_state = "critical"
    elif manual:
        expected_state = "manual_emergency"
    elif value >= WARNING_THRESHOLD:
        expected_state = "warning"
    else:
        expected_state = "normal"

    if data.get("state") != expected_state:
        return False, "État incohérent avec la mesure"

    return True, "OK"


# =====================================================
# RECONNEXION SERIE AUTOMATIQUE
# =====================================================
def serial_worker():
    while not stop_event.is_set():
        connected_at = None

        try:
            messages.put(("serial_status", "Connexion au port série..."))

            with serial.Serial(
                SERIAL_PORT,
                BAUD_RATE,
                timeout=1
            ) as connection:
                connected_at = time.monotonic()
                messages.put(("port_open", f"Port {SERIAL_PORT} ouvert"))

                # L'Arduino peut redémarrer à l'ouverture du port.
                while not stop_event.is_set():
                    raw = connection.readline()

                    if not raw:
                        continue

                    line = raw.decode(
                        "utf-8", errors="replace"
                    ).strip()

                    if not line:
                        continue

                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        # Les lignes illisibles immédiatement après
                        # l'ouverture peuvent provenir du redémarrage.
                        if time.monotonic() - connected_at < STARTUP_GRACE_SECONDS:
                            messages.put(("startup_noise", None))
                        else:
                            messages.put((
                                "anomaly",
                                "JSON malformé",
                                {"event": line[:200]}
                            ))
                        continue

                    if not isinstance(data, dict):
                        messages.put((
                            "anomaly",
                            "Le JSON reçu n'est pas un objet",
                            {"event": line[:200]}
                        ))
                        continue

                    messages.put(("data", data))

        except (SerialException, OSError) as exc:
            if not stop_event.is_set():
                messages.put(("serial_error", str(exc)))

        finally:
            messages.put(("port_closed", "Port série fermé"))

        if not stop_event.is_set():
            messages.put(("retry", "Nouvelle tentative dans 3 secondes"))
            stop_event.wait(RECONNECT_INTERVAL)


# =====================================================
# INTERFACE SCADA
# =====================================================
root = tk.Tk()
root.title("Mini-SCADA - Supervision et sécurité")
root.geometry("900x720")
root.minsize(700, 560)

style = ttk.Style()
style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"))
style.configure("Value.TLabel", font=("Segoe UI", 15, "bold"))
style.configure("Status.TLabel", font=("Segoe UI", 12, "bold"))

main = ttk.Frame(root, padding=18)
main.pack(fill="both", expand=True)

ttk.Label(
    main, text="SUPERVISION INDUSTRIELLE",
    style="Title.TLabel"
).pack(anchor="w")

ttk.Label(
    main, text="Arduino Uno | Niveau d'eau | USB série"
).pack(anchor="w", pady=(2, 12))

connection_var = tk.StringVar(value="Connexion en cours...")
ttk.Label(main, textvariable=connection_var).pack(
    anchor="w", pady=(0, 8)
)

watchdog_var = tk.StringVar(value="COMMUNICATION EN ATTENTE")
watchdog_label = ttk.Label(
    main, textvariable=watchdog_var, style="Status.TLabel"
)
watchdog_label.pack(anchor="w", pady=(0, 10))

# Mesures
sensor_frame = ttk.LabelFrame(main, text="Mesure du capteur", padding=12)
sensor_frame.pack(fill="x", pady=5)

value_var = tk.StringVar(value="--")
state_var = tk.StringVar(value="En attente de données")
freshness_var = tk.StringVar(value="Aucune mesure reçue")

ttk.Label(sensor_frame, text="Valeur analogique :").grid(
    row=0, column=0, sticky="w"
)
ttk.Label(
    sensor_frame, textvariable=value_var, style="Value.TLabel"
).grid(row=0, column=1, sticky="w", padx=12)

ttk.Label(sensor_frame, text="État du système :").grid(
    row=1, column=0, sticky="w", pady=(8, 0)
)
state_label = ttk.Label(
    sensor_frame, textvariable=state_var, style="Status.TLabel"
)
state_label.grid(row=1, column=1, sticky="w", padx=12, pady=(8, 0))

ttk.Label(
    sensor_frame, textvariable=freshness_var
).grid(row=2, column=0, columnspan=2, sticky="w", pady=(8, 0))

# Alarmes
alarm_frame = ttk.LabelFrame(main, text="État des alarmes", padding=12)
alarm_frame.pack(fill="x", pady=8)

water_var = tk.StringVar(value="Inconnue")
manual_var = tk.StringVar(value="Inconnue")
mute_var = tk.StringVar(value="Inconnue")

for index, (label, variable) in enumerate([
    ("Urgence eau :", water_var),
    ("Urgence manuelle :", manual_var),
    ("Buzzer en silence :", mute_var)
]):
    ttk.Label(alarm_frame, text=label).grid(
        row=index, column=0, sticky="w", pady=3
    )
    ttk.Label(alarm_frame, textvariable=variable).grid(
        row=index, column=1, sticky="w", padx=12, pady=3
    )

# Surveillance de sécurité
security_frame = ttk.LabelFrame(
    main, text="Surveillance de sécurité", padding=10
)
security_frame.pack(fill="x", pady=8)

anomaly_count = 0
anomaly_var = tk.StringVar(value="Anomalies détectées : 0")
security_status_var = tk.StringVar(value="Aucune anomalie détectée")

ttk.Label(
    security_frame, textvariable=anomaly_var,
    style="Value.TLabel"
).pack(anchor="w")

security_status_label = ttk.Label(
    security_frame, textvariable=security_status_var
)
security_status_label.pack(anchor="w", pady=(4, 0))

# Historique
history_frame = ttk.LabelFrame(
    main, text="Événements récents", padding=8
)
history_frame.pack(fill="both", expand=True, pady=5)

history = tk.Listbox(history_frame, height=8)
history.pack(fill="both", expand=True)

ttk.Label(
    main, text=f"Journal CSV : {LOG_FILE.name}"
).pack(anchor="w", pady=(8, 0))


# =====================================================
# ETAT DE SUPERVISION
# =====================================================
last_telemetry_time = None
communication_lost = True
port_available = False
last_valid_data = None
anomaly_count = 0


def add_history(message):
    stamp = datetime.now().strftime("%H:%M:%S")
    history.insert(0, f"[{stamp}] {message}")
    while history.size() > 100:
        history.delete(tk.END)


def register_anomaly(reason, details=None):
    global anomaly_count
    anomaly_count += 1
    anomaly_var.set(f"Anomalies détectées : {anomaly_count}")
    security_status_var.set(f"ANOMALIE : {reason}")
    security_status_label.configure(foreground="red")
    add_history(f"ALERTE SECURITE : {reason}")

    log_data = {"event": reason}
    if details:
        log_data.update(details)
    write_log("security_anomaly", log_data)


def display_telemetry(data):
    global last_telemetry_time, communication_lost, last_valid_data

    value = data["value"]
    state = data["state"]

    if communication_lost:
        communication_lost = False
        watchdog_var.set("COMMUNICATION OK")
        watchdog_label.configure(foreground="green")
        freshness_var.set("Mesure actuelle")
        add_history("Communication rétablie")
        write_log("communication_restored", {
            "event": "communication_restored"
        })

    last_telemetry_time = time.monotonic()
    last_valid_data = data

    value_var.set(str(value))
    state_var.set(state.replace("_", " ").upper())
    freshness_var.set("Mesure actuelle")

    water_var.set("ACTIVE" if data["water_emergency"] else "Inactive")
    manual_var.set("ACTIVE" if data["manual_emergency"] else "Inactive")
    mute_var.set("Oui" if data["alarm_muted"] else "Non")

    if data["emergency"]:
        state_label.configure(foreground="red")
    elif value >= WARNING_THRESHOLD:
        state_label.configure(foreground="#B8860B")
    else:
        state_label.configure(foreground="green")

    write_log("telemetry", data)


def handle_data(data):
    if data.get("sensor") == "water_level":
        valid, reason = validate_telemetry(data)
        if not valid:
            register_anomaly(reason, {
                "value": str(data.get("value", ""))[:100],
                "state": str(data.get("state", ""))[:100]
            })
            return

        display_telemetry(data)
        return

    allowed_events = {
        "system_started",
        "manual_emergency_activated",
        "manual_emergency_cleared",
        "rfid_authorized",
        "rfid_unauthorized",
        "alarm_mute_expired"
    }

    event = data.get("event")
    if isinstance(event, str) and event in allowed_events:
        add_history(f"Événement : {event}")
        write_log("event", {"event": event})
    else:
        register_anomaly("Message ou événement inconnu")


def check_watchdog():
    global communication_lost

    if last_telemetry_time is None:
        if not communication_lost:
            communication_lost = True
        watchdog_var.set(
            "COMMUNICATION EN ATTENTE"
            if port_available
            else "COMMUNICATION PERDUE"
        )
        watchdog_label.configure(foreground="#B8860B" if port_available else "red")
        freshness_var.set("Aucune télémétrie valide reçue")

    elif time.monotonic() - last_telemetry_time > WATCHDOG_TIMEOUT:
        if not communication_lost:
            communication_lost = True
            watchdog_var.set("COMMUNICATION PERDUE")
            watchdog_label.configure(foreground="red")
            freshness_var.set("Dernière mesure ancienne — ne pas s'y fier")
            add_history("ALERTE : communication perdue")
            write_log("communication_lost", {
                "event": "communication_lost",
                "value": last_valid_data.get("value", "")
                if last_valid_data else ""
            })

    elif not communication_lost:
        watchdog_var.set("COMMUNICATION OK")
        watchdog_label.configure(foreground="green")

    root.after(250, check_watchdog)


def process_messages():
    global port_available

    try:
        while True:
            kind, *payload = messages.get_nowait()

            if kind == "serial_status":
                connection_var.set(payload[0])

            elif kind == "port_open":
                port_available = True
                connection_var.set(payload[0])
                add_history(payload[0])

            elif kind == "connection_error":
                port_available = False
                connection_var.set("Erreur de connexion série")
                add_history(f"ERREUR : {payload[0]}")

            elif kind == "serial_error":
                port_available = False
                connection_var.set("Port série interrompu — reconnexion...")
                add_history(f"Connexion interrompue : {payload[0]}")

            elif kind == "port_closed":
                port_available = False

            elif kind == "retry":
                connection_var.set(payload[0])

            elif kind == "startup_noise":
                # Bruit de démarrage informatif, non compté comme anomalie.
                pass

            elif kind == "anomaly":
                register_anomaly(payload[0], payload[1])

            elif kind == "log_error":
                add_history(f"ERREUR JOURNAL : {payload[0]}")

            elif kind == "data":
                handle_data(payload[0])

    except queue.Empty:
        pass

    if not stop_event.is_set():
        root.after(100, process_messages)


def close_application():
    stop_event.set()
    root.destroy()


root.protocol("WM_DELETE_WINDOW", close_application)
threading.Thread(target=serial_worker, daemon=True).start()
root.after(100, process_messages)
root.after(250, check_watchdog)
root.mainloop()
