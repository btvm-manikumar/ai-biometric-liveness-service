from datetime import datetime, timedelta, timezone
import random
from typing import List

from app.schemas.liveness import SyntheticMeasurement


class SyntheticDataGenerator:
    """Creates deterministic records for local development and tests only."""

    def __init__(self, seed: int = 7):
        self._random = random.Random(seed)

    def create_measurement(
        self,
        user_id: str = "SYNTH-USER-001",
        session_id: str = "SYNTH-SESSION-001",
        device_id: str = "SYNTH-DEVICE-001",
        timestamp: datetime | None = None,
    ) -> SyntheticMeasurement:
        return self.generate_valid_sample(
            user_id=user_id,
            session_id=session_id,
            device_id=device_id,
            timestamp=timestamp,
        )

    def _sample(
        self,
        scenario: str,
        face_score: tuple[float, float],
        liveness_score: tuple[float, float],
        quality: str,
        user_id: str,
        session_id: str,
        device_id: str,
        timestamp: datetime | None,
    ) -> SyntheticMeasurement:
        timestamp = timestamp or datetime(2026, 9, 11, 19, 30, tzinfo=timezone.utc)
        return SyntheticMeasurement(
            scenario=scenario,
            userId=user_id,
            sessionId=session_id,
            deviceId=device_id,
            faceMatchScore=round(self._random.uniform(*face_score), 2),
            livenessScore=round(self._random.uniform(*liveness_score), 2),
            timestamp=timestamp,
            measurementSource="SYNTHETIC_CAMERA",
            measurementQuality=quality,
        )

    def generate_valid_sample(
        self,
        user_id: str = "SYNTH-USER-001",
        session_id: str = "SYNTH-SESSION-001",
        device_id: str = "SYNTH-DEVICE-001",
        timestamp: datetime | None = None,
    ) -> SyntheticMeasurement:
        return self._sample(
            "VALID",
            (0.86, 0.99),
            (0.86, 0.99),
            "GOOD",
            user_id,
            session_id,
            device_id,
            timestamp,
        )

    def generate_face_failure_sample(
        self,
        user_id: str = "SYNTH-USER-001",
        session_id: str = "SYNTH-SESSION-001",
        device_id: str = "SYNTH-DEVICE-001",
        timestamp: datetime | None = None,
    ) -> SyntheticMeasurement:
        return self._sample(
            "FACE_FAILURE",
            (0.20, 0.79),
            (0.86, 0.99),
            "GOOD",
            user_id,
            session_id,
            device_id,
            timestamp,
        )

    def generate_liveness_failure_sample(
        self,
        user_id: str = "SYNTH-USER-001",
        session_id: str = "SYNTH-SESSION-001",
        device_id: str = "SYNTH-DEVICE-001",
        timestamp: datetime | None = None,
    ) -> SyntheticMeasurement:
        return self._sample(
            "LIVENESS_FAILURE",
            (0.86, 0.99),
            (0.20, 0.79),
            "GOOD",
            user_id,
            session_id,
            device_id,
            timestamp,
        )

    def generate_both_failure_sample(
        self,
        user_id: str = "SYNTH-USER-001",
        session_id: str = "SYNTH-SESSION-001",
        device_id: str = "SYNTH-DEVICE-001",
        timestamp: datetime | None = None,
    ) -> SyntheticMeasurement:
        return self._sample(
            "BOTH_FAILURE",
            (0.20, 0.79),
            (0.20, 0.79),
            "FAIR",
            user_id,
            session_id,
            device_id,
            timestamp,
        )

    def generate_invalid_sample(
        self,
        user_id: str = "SYNTH-INVALID-USER-001",
        session_id: str = "SYNTH-INVALID-SESSION-001",
        device_id: str = "SYNTH-INVALID-DEVICE-001",
        timestamp: datetime | None = None,
    ) -> SyntheticMeasurement:
        return self._sample(
            "INVALID",
            (1.01, 1.20),
            (0.86, 0.99),
            "POOR",
            user_id,
            session_id,
            device_id,
            timestamp,
        )

    def create_dataset(self, count: int = 3) -> List[SyntheticMeasurement]:
        start = datetime(2026, 9, 11, 19, 30, tzinfo=timezone.utc)
        scenarios = (
            self.generate_valid_sample,
            self.generate_face_failure_sample,
            self.generate_liveness_failure_sample,
            self.generate_both_failure_sample,
            self.generate_invalid_sample,
        )
        records = []
        for index in range(1, count + 1):
            scenario_generator = scenarios[(index - 1) % len(scenarios)]
            records.append(
                scenario_generator(
                    user_id=f"SYNTH-USER-{index:03d}",
                    session_id=f"SYNTH-SESSION-{index:03d}",
                    device_id=f"SYNTH-DEVICE-{index:03d}",
                    timestamp=start + timedelta(minutes=index - 1),
                )
            )
        return records

    def create_development_dataset(self) -> List[SyntheticMeasurement]:
        """Create the fixed 100-record development distribution."""
        scenario_counts = (
            (self.generate_valid_sample, 25),
            (self.generate_face_failure_sample, 20),
            (self.generate_liveness_failure_sample, 20),
            (self.generate_both_failure_sample, 15),
            (self.generate_invalid_sample, 20),
        )
        start = datetime(2026, 9, 11, 19, 30, tzinfo=timezone.utc)
        records = []
        index = 1
        for scenario_generator, count in scenario_counts:
            for _ in range(count):
                records.append(
                    scenario_generator(
                        user_id=f"SYNTH-USER-{index:03d}",
                        session_id=f"SYNTH-SESSION-{index:03d}",
                        device_id=f"SYNTH-DEVICE-{index:03d}",
                        timestamp=start + timedelta(minutes=index - 1),
                    )
                )
                index += 1
        return records


_default_generator = SyntheticDataGenerator()


def generate_valid_sample() -> SyntheticMeasurement:
    return _default_generator.generate_valid_sample()


def generate_face_failure_sample() -> SyntheticMeasurement:
    return _default_generator.generate_face_failure_sample()


def generate_liveness_failure_sample() -> SyntheticMeasurement:
    return _default_generator.generate_liveness_failure_sample()


def generate_both_failure_sample() -> SyntheticMeasurement:
    return _default_generator.generate_both_failure_sample()


def generate_invalid_sample() -> SyntheticMeasurement:
    return _default_generator.generate_invalid_sample()


def generate_development_dataset() -> List[SyntheticMeasurement]:
    return _default_generator.create_development_dataset()
