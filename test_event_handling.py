import ast
import unittest
from pathlib import Path

SOURCE = Path(__file__).with_name("scada.py")


def load_handle_data():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8-sig"))

    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "handle_data":
            isolated = ast.Module(body=[node], type_ignores=[])
            namespace = {
                "validate_telemetry": lambda data: (True, "OK"),
                "display_telemetry": lambda data: None,
                "register_anomaly": lambda reason, details=None:
                    captured.append((reason, details)),
                "add_history": lambda message: history.append(message),
                "write_log": lambda kind, data: logs.append((kind, data)),
            }
            exec(compile(isolated, str(SOURCE), "exec"), namespace)
            return namespace["handle_data"]

    raise RuntimeError("Fonction handle_data introuvable")


class TestEventHandling(unittest.TestCase):

    def setUp(self):
        global captured, history, logs
        captured = []
        history = []
        logs = []
        self.handle_data = load_handle_data()

    def test_authorized_event_is_logged(self):
        self.handle_data({"event": "rfid_authorized"})
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0][0], "event")
        self.assertEqual(logs[0][1]["event"], "rfid_authorized")

    def test_unknown_event_is_anomaly(self):
        self.handle_data({"event": "unknown_event"})
        self.assertEqual(len(captured), 1)
        self.assertEqual(captured[0][0], "Message ou événement inconnu")

    def test_unknown_sensor_is_anomaly(self):
        self.handle_data({"sensor": "unknown_sensor", "value": 10})
        self.assertEqual(len(captured), 1)
        self.assertEqual(captured[0][0], "Message ou événement inconnu")

    def test_all_allowed_events_are_accepted(self):
        allowed = [
            "system_started",
            "manual_emergency_activated",
            "manual_emergency_cleared",
            "rfid_authorized",
            "rfid_unauthorized",
            "alarm_mute_expired",
        ]

        for event in allowed:
            with self.subTest(event=event):
                self.handle_data({"event": event})

        self.assertEqual(len(logs), len(allowed))
        self.assertEqual(len(captured), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
