from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

from app.config.settings import Settings
from app.schemas.liveness import BiometricSession, SyntheticMeasurement
from app.services.biometric_service import BiometricSessionService
from app.services.liveness_service import LivenessVerificationService


GOOD_MEASUREMENT = SyntheticMeasurement(
    userId="SYNTH-USER-001",
    sessionId="SYNTH-SESSION-001",
    deviceId="SYNTH-DEVICE-001",
    faceMatchScore=0.94,
    livenessScore=0.91,
    timestamp="2026-09-11T19:30:00Z",
    measurementSource="SYNTHETIC_CAMERA",
    measurementQuality="GOOD",
)
TEST_NOW = datetime(2026, 9, 11, 19, 30, tzinfo=timezone.utc)
DATASET_PATH = Path(__file__).parents[2] / "data" / "synthetic_liveness_data.json"


def service():
    sessions = BiometricSessionService()
    sessions.register_synthetic_session(
        BiometricSession(
            userId="SYNTH-USER-001",
            sessionId="SYNTH-SESSION-001",
            deviceId="SYNTH-DEVICE-001",
            createdAt=TEST_NOW,
            expiresAt=TEST_NOW + timedelta(minutes=10),
            authenticated=True,
        )
    )
    return LivenessVerificationService(sessions, Settings(), clock=lambda: TEST_NOW)


def test_accepts_matching_synthetic_measurement():
    result = service().verify(GOOD_MEASUREMENT)

    assert result.authenticated is True
    assert result.failure_reason is None
    assert result.face_verified is True
    assert result.liveness_verified is True
    assert result.status == "VERIFIED"


def test_success_marks_session_liveness_verified():
    sessions = BiometricSessionService()
    session = BiometricSession(
        userId="SYNTH-USER-001",
        sessionId="SYNTH-SESSION-001",
        deviceId="SYNTH-DEVICE-001",
        createdAt=TEST_NOW,
        expiresAt=TEST_NOW + timedelta(minutes=10),
    )
    sessions.register_synthetic_session(session)

    LivenessVerificationService(sessions, Settings(), clock=lambda: TEST_NOW).verify(GOOD_MEASUREMENT)

    assert session.liveness_verified is True


def test_rejects_user_mismatch():
    measurement = GOOD_MEASUREMENT.model_copy(update={"user_id": "SYNTH-USER-999"})

    result = service().verify(measurement)

    assert result.authenticated is False
    assert result.failure_reason == "USER_MISMATCH"


def test_rejects_low_liveness_score():
    measurement = GOOD_MEASUREMENT.model_copy(update={"liveness_score": 0.4})

    result = service().verify(measurement)

    assert result.authenticated is False
    assert result.failure_reason == "LIVENESS_BELOW_THRESHOLD"


def test_rejects_device_mismatch():
    measurement = GOOD_MEASUREMENT.model_copy(update={"device_id": "SYNTH-DEVICE-999"})

    result = service().verify(measurement)

    assert result.authenticated is False
    assert result.failure_reason == "DEVICE_MISMATCH"


def test_settings_use_synthetic_engineering_defaults():
    config = Settings()

    assert config.face_match_threshold == 0.80
    assert config.liveness_threshold == 0.80
    assert config.session_expiry_minutes == 10
    assert config.timestamp_tolerance_seconds == 300


def test_service_uses_injected_face_threshold():
    sessions = BiometricSessionService()
    sessions.register_synthetic_session(
        BiometricSession(
            userId="SYNTH-USER-001",
            sessionId="SYNTH-SESSION-001",
            deviceId="SYNTH-DEVICE-001",
            createdAt=TEST_NOW,
            expiresAt=TEST_NOW + timedelta(minutes=10),
            authenticated=True,
        )
    )
    config = Settings()
    config.face_match_threshold = 0.95
    service_with_custom_threshold = LivenessVerificationService(
        sessions,
        config,
        clock=lambda: TEST_NOW,
    )

    result = service_with_custom_threshold.verify(GOOD_MEASUREMENT)

    assert result.authenticated is False
    assert result.failure_reason == "FACE_MATCH_BELOW_THRESHOLD"


def test_rejects_expired_session():
    sessions = BiometricSessionService()
    sessions.register_synthetic_session(
        BiometricSession(
            userId="SYNTH-USER-001",
            sessionId="SYNTH-SESSION-001",
            deviceId="SYNTH-DEVICE-001",
            createdAt=TEST_NOW - timedelta(minutes=11),
            expiresAt=TEST_NOW - timedelta(minutes=1),
        )
    )

    result = LivenessVerificationService(sessions, Settings(), clock=lambda: TEST_NOW).verify(GOOD_MEASUREMENT)

    assert result.status == "FAILED"
    assert result.failure_reason == "SESSION_EXPIRED"


def test_rejects_timestamp_outside_configured_tolerance():
    measurement = GOOD_MEASUREMENT.model_copy(update={"timestamp": TEST_NOW + timedelta(seconds=301)})

    result = service().verify(measurement)

    assert result.failure_reason == "TIMESTAMP_OUTSIDE_TOLERANCE"


def test_rejects_out_of_range_scores():
    measurement = GOOD_MEASUREMENT.model_copy(update={"face_match_score": 1.1})

    result = service().verify(measurement)

    assert result.failure_reason == "FACE_SCORE_OUT_OF_RANGE"


def test_rejects_missing_measurement_source_and_quality():
    missing_source = GOOD_MEASUREMENT.model_copy(update={"measurement_source": ""})
    missing_quality = GOOD_MEASUREMENT.model_copy(update={"measurement_quality": ""})

    source_result = service().verify(missing_source)
    quality_result = service().verify(missing_quality)

    assert source_result.failure_reason == "MEASUREMENT_SOURCE_MISSING"
    assert quality_result.failure_reason == "MEASUREMENT_QUALITY_MISSING"


def test_every_dataset_record_matches_its_expected_scenario():
    records = json.loads(DATASET_PATH.read_text(encoding="utf-8"))

    for record in records:
        timestamp = datetime.fromisoformat(record["timestamp"].replace("Z", "+00:00"))
        sessions = BiometricSessionService()
        sessions.register_synthetic_session(
            BiometricSession(
                userId=record["userId"],
                sessionId=record["sessionId"],
                deviceId=record["deviceId"],
                createdAt=timestamp,
                expiresAt=timestamp + timedelta(minutes=10),
            )
        )
        result = LivenessVerificationService(
            sessions,
            Settings(),
            clock=lambda timestamp=timestamp: timestamp,
        ).verify(SyntheticMeasurement.model_validate(record))

        if record["scenario"] == "VALID":
            assert result.face_verified is True
            assert result.liveness_verified is True
            assert result.authenticated is True
        elif record["scenario"] == "FACE_FAILURE":
            assert result.face_verified is False
            assert result.authenticated is False
        elif record["scenario"] == "LIVENESS_FAILURE":
            assert result.liveness_verified is False
            assert result.authenticated is False
        elif record["scenario"] == "BOTH_FAILURE":
            assert result.face_verified is False
            assert result.liveness_verified is False
            assert result.authenticated is False
        else:
            assert result.status == "FAILED"
            assert result.authenticated is False
            assert result.failure_reason == "FACE_SCORE_OUT_OF_RANGE"
