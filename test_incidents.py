import csv
import json
import tempfile
import unittest
from pathlib import Path


def validate_message(raw):
    try:
        msg = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return False, "JSON invalide"

    if not isinstance(msg, dict):
        return False, "Le message doit être un objet JSON"

    if msg.get("sensor") != "water_level":
        return False, "Capteur invalide"

    value = msg.get("value")
    if isinstance(value, bool) or not isinstance(value, int):
        return False, "Mesure non entière"

    if not 0 <= value <= 1023:
        return False, "Mesure hors limites"

    if msg.get("warning_threshold") != 150:
        return False, "Seuil warning invalide"

    if msg.get("critical_threshold") != 250:
        return False, "Seuil critique invalide"

    for field in ("emergency", "manual_emergency",
                  "water_emergency", "alarm_muted"):
        if not isinstance(msg.get(field), bool):
            return False, f"Champ {field} invalide"

    expected_water_emergency = value >= 250
    if msg["water_emergency"] != expected_water_emergency:
        return False, "Urgence eau incohérente"

    expected_emergency = (
        msg["manual_emergency"] or msg["water_emergency"]
    )
    if msg["emergency"] != expected_emergency:
        return False, "Urgence globale incohérente"

    expected_state = (
        "CRITICAL" if value >= 250
        else "WARNING" if value >= 150
        else "NORMAL"
    )
    if msg.get("state") != expected_state:
        return False, "État incohérent"

    return True, "OK"


def write_event(csv_path, event, details):
    file_path = Path(csv_path)
    exists = file_path.exists()

    with file_path.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file, fieldnames=["event", "details"]
        )
        if not exists or file_path.stat().st_size == 0:
            writer.writeheader()
        writer.writerow({"event": event, "details": details})


def make_message(value=100, manual=False, muted=False):
    water_emergency = value >= 250
    emergency = manual or water_emergency
    state = (
        "CRITICAL" if value >= 250
        else "WARNING" if value >= 150
        else "NORMAL"
    )
    return json.dumps({
        "sensor": "water_level",
        "value": value,
        "state": state,
        "emergency": emergency,
        "manual_emergency": manual,
        "water_emergency": water_emergency,
        "warning_threshold": 150,
        "critical_threshold": 250,
        "alarm_muted": muted
    })


class TestIncidentSimulation(unittest.TestCase):

    def test_normal_message(self):
        ok, reason = validate_message(make_message(100))
        self.assertTrue(ok, reason)

    def test_warning_message(self):
        ok, reason = validate_message(make_message(180))
        self.assertTrue(ok, reason)

    def test_critical_message(self):
        ok, reason = validate_message(make_message(300))
        self.assertTrue(ok, reason)

    def test_manual_emergency(self):
        ok, reason = validate_message(make_message(100, manual=True))
        self.assertTrue(ok, reason)

    def test_malformed_json(self):
        ok, _ = validate_message('{"value":')
        self.assertFalse(ok)

    def test_value_above_sensor_range(self):
        ok, _ = validate_message(make_message(1200))
        self.assertFalse(ok)

    def test_inconsistent_emergency(self):
        msg = json.loads(make_message(100))
        msg["emergency"] = True
        ok, _ = validate_message(json.dumps(msg))
        self.assertFalse(ok)

    def test_csv_event_is_recorded(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "events.csv"

            write_event(csv_path, "ANOMALY", "JSON invalide")
            write_event(csv_path, "EMERGENCY", "Urgence manuelle")

            with csv_path.open(
                "r", newline="", encoding="utf-8"
            ) as file:
                rows = list(csv.DictReader(file))

            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["event"], "ANOMALY")
            self.assertEqual(rows[1]["event"], "EMERGENCY")


if __name__ == "__main__":
    unittest.main(verbosity=2)
