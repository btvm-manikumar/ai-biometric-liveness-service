from datetime import datetime, timedelta, timezone

import pytest

from app.config.settings import Settings
from app.schemas.liveness import BiometricSession
from app.services.biometric_service import BiometricSessionService
from app.services.spo2_service import Spo2Service
from app.synthetic.spo2_generator import (
	generate_attention_sample,
	generate_critical_sample,
	generate_low_sample,
	generate_normal_sample,
)


TEST_NOW = datetime(2026, 9, 15, 16, 0, tzinfo=timezone.utc)
USER_ID = "SYNTH-USER-001"
SESSION_ID = "SYNTH-SESSION-001"
DEVICE_ID = "SYNTH-DEVICE-001"


def create_service() -> Spo2Service:
	sessions = BiometricSessionService()
	sessions.register_synthetic_session(
		BiometricSession(
			userId=USER_ID,
			sessionId=SESSION_ID,
			deviceId=DEVICE_ID,
			createdAt=TEST_NOW,
			expiresAt=TEST_NOW + timedelta(minutes=10),
		)
	)
	return Spo2Service(sessions, Settings(), clock=lambda: TEST_NOW)


def test_analyzes_normal_spo2():
	result = create_service().analyze(generate_normal_sample())

	assert result.status == "NORMAL"
	assert result.measurement_accepted is True


def test_analyzes_attention_spo2():
	result = create_service().analyze(generate_attention_sample())

	assert result.status == "ATTENTION_REQUIRED"
	assert result.measurement_accepted is True


def test_analyzes_low_spo2():
	result = create_service().analyze(generate_low_sample())

	assert result.status == "LOW"
	assert result.measurement_accepted is True


def test_analyzes_critical_spo2():
	result = create_service().analyze(generate_critical_sample())

	assert result.status == "CRITICAL"
	assert result.measurement_accepted is True


@pytest.mark.parametrize("spo2", [-1, 101])
def test_rejects_spo2_outside_valid_range(spo2):
	measurement = generate_normal_sample().model_copy(update={"spo2": spo2})

	result = create_service().analyze(measurement)

	assert result.status == "INVALID"
	assert result.message == "SPO2_OUT_OF_RANGE"
	assert result.measurement_accepted is False


def test_rejects_missing_session():
	measurement = generate_normal_sample().model_copy(update={"session_id": "SYNTH-SESSION-MISSING"})

	result = create_service().analyze(measurement)

	assert result.message == "SESSION_NOT_FOUND"
	assert result.measurement_accepted is False


def test_rejects_wrong_user():
	measurement = generate_normal_sample().model_copy(update={"user_id": "SYNTH-USER-999"})

	result = create_service().analyze(measurement)

	assert result.message == "USER_MISMATCH"
	assert result.measurement_accepted is False


def test_rejects_wrong_device():
	measurement = generate_normal_sample().model_copy(update={"device_id": "SYNTH-DEVICE-999"})

	result = create_service().analyze(measurement)

	assert result.message == "DEVICE_MISMATCH"
	assert result.measurement_accepted is False


def test_rejects_timestamp_outside_tolerance():
	measurement = generate_normal_sample().model_copy(
		update={"timestamp": TEST_NOW + timedelta(seconds=Settings().timestamp_tolerance_seconds + 1)}
	)

	result = create_service().analyze(measurement)

	assert result.message == "TIMESTAMP_OUTSIDE_TOLERANCE"
	assert result.measurement_accepted is False


def test_rejects_poor_measurement_quality():
	measurement = generate_normal_sample().model_copy(update={"measurement_quality": "UNUSABLE"})

	result = create_service().analyze(measurement)

	assert result.message == "MEASUREMENT_QUALITY_INVALID"
	assert result.measurement_accepted is False


@pytest.mark.parametrize(
	("spo2", "expected_status"),
	[
		(95, "NORMAL"),
		(90, "ATTENTION_REQUIRED"),
		(80, "LOW"),
	],
)
def test_exact_threshold_values_use_configured_status_boundaries(spo2, expected_status):
	measurement = generate_normal_sample().model_copy(update={"spo2": spo2})

	result = create_service().analyze(measurement)

	assert result.status == expected_status
	assert result.measurement_accepted is True
