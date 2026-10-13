import ast
import csv
import tempfile
import unittest
from pathlib import Path
from datetime import datetime


SOURCE = Path(__file__).with_name("scada.py")


def load_write_log():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8-sig"))

    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "write_log":
            isolated = ast.Module(body=[node], type_ignores=[])
            namespace = {
                "csv": csv,
                "datetime": datetime,
                "messages": type("Messages", (), {
                    "put": staticmethod(lambda message: None)
                })(),
                "LOG_FIELDS": [
                    "timestamp", "type", "value", "state",
                    "emergency", "manual_emergency",
                    "water_emergency", "alarm_muted", "event"
                ],
                "LOG_FILE": None,
            }
            exec(compile(isolated, str(SOURCE), "exec"), namespace)
            return namespace["write_log"], namespace

    raise RuntimeError("Fonction write_log introuvable")


write_log, namespace = load_write_log()


class TestRealCsvLogging(unittest.TestCase):

    def test_event_is_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test_history.csv"
            namespace["LOG_FILE"] = path

            write_log("security_anomaly", {
                "event": "Test anomaly",
                "value": "1200"
            })

            with path.open(
                "r", newline="", encoding="utf-8"
            ) as file:
                rows = list(csv.DictReader(file))

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["type"], "security_anomaly")
            self.assertEqual(rows[0]["event"], "Test anomaly")
            self.assertEqual(rows[0]["value"], "1200")
            self.assertTrue(rows[0]["timestamp"])

    def test_multiple_events_append(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test_history.csv"
            namespace["LOG_FILE"] = path

            write_log("telemetry", {"value": 100})
            write_log("communication_lost", {
                "event": "communication_lost"
            })

            with path.open(
                "r", newline="", encoding="utf-8"
            ) as file:
                rows = list(csv.DictReader(file))

            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["type"], "telemetry")
            self.assertEqual(rows[1]["type"], "communication_lost")


if __name__ == "__main__":
    unittest.main(verbosity=2)
