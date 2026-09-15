"""Deterministic synthetic SpO2 data generation for Task 2."""

from datetime import datetime, timezone

from app.schemas.spo2 import Spo2Measurement


class Spo2Generator:
    """Creates fixed synthetic SpO2 records for development and tests."""

    _timestamp = datetime(2026, 9, 15, 16, 0, tzinfo=timezone.utc)

    def _create_sample(self, scenario: str, spo2: float, quality: str) -> Spo2Measurement:
        return Spo2Measurement(
            scenario=scenario,
            userId="SYNTH-USER-001",
            sessionId="SYNTH-SESSION-001",
            deviceId="SYNTH-DEVICE-001",
            spo2=spo2,
            timestamp=self._timestamp,
            measurementSource="SYNTHETIC_SPO2_DEVICE",
            measurementQuality=quality,
        )

    def generate_normal_sample(self) -> Spo2Measurement:
        return self._create_sample("NORMAL", 98, "GOOD")

    def generate_attention_sample(self) -> Spo2Measurement:
        return self._create_sample("ATTENTION", 93, "FAIR")

    def generate_low_sample(self) -> Spo2Measurement:
        return self._create_sample("LOW", 88, "FAIR")

    def generate_critical_sample(self) -> Spo2Measurement:
        return self._create_sample("CRITICAL", 75, "POOR")

    def generate_invalid_sample(self) -> Spo2Measurement:
        return self._create_sample("INVALID", 101, "POOR")


_default_generator = Spo2Generator()


def generate_normal_sample() -> Spo2Measurement:
    return _default_generator.generate_normal_sample()


def generate_attention_sample() -> Spo2Measurement:
    return _default_generator.generate_attention_sample()


def generate_low_sample() -> Spo2Measurement:
    return _default_generator.generate_low_sample()


def generate_critical_sample() -> Spo2Measurement:
    return _default_generator.generate_critical_sample()


def generate_invalid_sample() -> Spo2Measurement:
    return _default_generator.generate_invalid_sample()
