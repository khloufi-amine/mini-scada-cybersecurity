import ast
import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import scada


class TestRealScadaValidation(unittest.TestCase):

    def valid_message(self, value=100, manual=False):
        water = value >= scada.CRITICAL_THRESHOLD
        state = (
            "critical" if water
            else "manual_emergency" if manual
            else "warning" if value >= scada.WARNING_THRESHOLD
            else "normal"
        )
        return {
            "sensor": "water_level",
            "value": value,
            "state": state,
            "emergency": water or manual,
            "manual_emergency": manual,
            "water_emergency": water,
            "warning_threshold": scada.WARNING_THRESHOLD,
            "critical_threshold": scada.CRITICAL_THRESHOLD,
            "alarm_muted": False,
        }

    def test_valid_normal_message(self):
        ok, reason = scada.validate_telemetry(self.valid_message(100))
        self.assertTrue(ok, reason)

    def test_warning_message(self):
        ok, reason = scada.validate_telemetry(self.valid_message(180))
        self.assertTrue(ok, reason)

    def test_critical_message(self):
        ok, reason = scada.validate_telemetry(self.valid_message(300))
        self.assertTrue(ok, reason)

    def test_manual_emergency(self):
        ok, reason = scada.validate_telemetry(
            self.valid_message(100, manual=True)
        )
        self.assertTrue(ok, reason)

    def test_value_out_of_range_rejected(self):
        msg = self.valid_message(100)
        msg["value"] = 1200
        ok, _ = scada.validate_telemetry(msg)
        self.assertFalse(ok)

    def test_boolean_value_rejected(self):
        msg = self.valid_message(100)
        msg["value"] = True
        ok, _ = scada.validate_telemetry(msg)
        self.assertFalse(ok)

    def test_inconsistent_emergency_rejected(self):
        msg = self.valid_message(100)
        msg["emergency"] = True
        ok, _ = scada.validate_telemetry(msg)
        self.assertFalse(ok)

    def test_wrong_threshold_rejected(self):
        msg = self.valid_message(100)
        msg["critical_threshold"] = 999
        ok, _ = scada.validate_telemetry(msg)
        self.assertFalse(ok)


class TestRealScadaCsv(unittest.TestCase):

    def test_write_log_writes_event_to_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test_history.csv"

            with patch.object(scada, "LOG_FILE", path):
                scada.write_log(
                    "security_anomaly",
                    {"event": "Test anomaly", "value": "1200"}
                )

            with path.open(
                "r", newline="", encoding="utf-8"
            ) as file:
                rows = list(csv.DictReader(file))

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["type"], "security_anomaly")
            self.assertEqual(rows[0]["event"], "Test anomaly")
            self.assertEqual(rows[0]["value"], "1200")


if __name__ == "__main__":
    unittest.main(verbosity=2)
