import ast
import unittest
from pathlib import Path

SOURCE = Path(__file__).with_name("scada.py")


def load_validation_function():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8-sig"))

    names = {
        "WARNING_THRESHOLD": 150,
        "CRITICAL_THRESHOLD": 250,
    }

    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "validate_telemetry":
            isolated = ast.Module(body=[node], type_ignores=[])
            code = compile(isolated, str(SOURCE), "exec")
            exec(code, names)
            return names["validate_telemetry"]

    raise RuntimeError("Fonction validate_telemetry introuvable")


validate_telemetry = load_validation_function()


def make_message(value=100, manual=False):
    water = value >= 250
    state = (
        "critical" if water
        else "manual_emergency" if manual
        else "warning" if value >= 150
        else "normal"
    )
    return {
        "sensor": "water_level",
        "value": value,
        "state": state,
        "emergency": water or manual,
        "manual_emergency": manual,
        "water_emergency": water,
        "warning_threshold": 150,
        "critical_threshold": 250,
        "alarm_muted": False,
    }


class TestRealValidation(unittest.TestCase):

    def test_normal(self):
        self.assertTrue(validate_telemetry(make_message(100))[0])

    def test_warning(self):
        self.assertTrue(validate_telemetry(make_message(180))[0])

    def test_critical(self):
        self.assertTrue(validate_telemetry(make_message(300))[0])

    def test_manual_emergency(self):
        self.assertTrue(validate_telemetry(make_message(100, True))[0])

    def test_value_too_high(self):
        msg = make_message(100)
        msg["value"] = 1200
        self.assertFalse(validate_telemetry(msg)[0])

    def test_boolean_is_not_integer_measurement(self):
        msg = make_message(100)
        msg["value"] = True
        self.assertFalse(validate_telemetry(msg)[0])

    def test_inconsistent_emergency(self):
        msg = make_message(100)
        msg["emergency"] = True
        self.assertFalse(validate_telemetry(msg)[0])

    def test_wrong_threshold(self):
        msg = make_message(100)
        msg["critical_threshold"] = 999
        self.assertFalse(validate_telemetry(msg)[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
