import json
import unittest

WARNING_THRESHOLD = 150
CRITICAL_THRESHOLD = 250


def validate_telemetry(data):
    if not isinstance(data, dict):
        return False, "JSON doit être un objet"

    if data.get("sensor") != "water_level":
        return False, "Capteur inconnu"

    value = data.get("value")
    if type(value) is not int or not 0 <= value <= 1023:
        return False, "Mesure invalide"

    if data.get("warning_threshold") != WARNING_THRESHOLD:
        return False, "Seuil avertissement incorrect"

    if data.get("critical_threshold") != CRITICAL_THRESHOLD:
        return False, "Seuil critique incorrect"

    fields = (
        "emergency",
        "manual_emergency",
        "water_emergency",
        "alarm_muted",
    )

    for field in fields:
        if type(data.get(field)) is not bool:
            return False, f"Champ invalide : {field}"

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


def parse_json_message(raw_message):
    try:
        data = json.loads(raw_message)
    except json.JSONDecodeError:
        return False, "JSON malformé"

    return validate_telemetry(data)


def valid_message(value=50, state="normal"):
    water = value >= CRITICAL_THRESHOLD
    manual = False

    if water:
        state = "critical"
    elif value >= WARNING_THRESHOLD:
        state = "warning"

    return {
        "sensor": "water_level",
        "value": value,
        "state": state,
        "emergency": water or manual,
        "manual_emergency": manual,
        "water_emergency": water,
        "warning_threshold": WARNING_THRESHOLD,
        "critical_threshold": CRITICAL_THRESHOLD,
        "alarm_muted": False,
    }


class TestScadaSecurity(unittest.TestCase):

    def test_valid_message_is_accepted(self):
        accepted, reason = parse_json_message(
            json.dumps(valid_message())
        )
        self.assertTrue(accepted, reason)

    def test_value_above_adc_range_is_rejected(self):
        message = valid_message()
        message["value"] = 1200
        accepted, reason = parse_json_message(json.dumps(message))
        self.assertFalse(accepted)
        self.assertEqual(reason, "Mesure invalide")

    def test_malformed_json_is_rejected(self):
        accepted, reason = parse_json_message(
            '{"sensor":"water_level","value":50'
        )
        self.assertFalse(accepted)
        self.assertEqual(reason, "JSON malformé")

    def test_inconsistent_state_is_rejected(self):
        message = valid_message()
        message["state"] = "critical"
        accepted, reason = parse_json_message(json.dumps(message))
        self.assertFalse(accepted)
        self.assertEqual(reason, "État incohérent avec la mesure")

    def test_string_measurement_is_rejected(self):
        message = valid_message()
        message["value"] = "50"
        accepted, reason = parse_json_message(json.dumps(message))
        self.assertFalse(accepted)
        self.assertEqual(reason, "Mesure invalide")


if __name__ == "__main__":
    print("=== TESTS DE CYBERSECURITE SCADA ===")
    unittest.main(verbosity=2)
