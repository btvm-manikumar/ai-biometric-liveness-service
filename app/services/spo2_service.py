"""Synthetic SpO2 validation and engineering-status analysis."""

from datetime import datetime, timezone
from typing import Callable

from app.config.settings import Settings
from app.schemas.liveness import BiometricSession
from app.schemas.spo2 import Spo2AnalysisResponse, Spo2Measurement
from app.services.biometric_service import BiometricSessionService


class Spo2Service:
    """Validates synthetic SpO2 measurements against an in-memory session."""

    def __init__(
        self,
        session_service: BiometricSessionService,
        config: Settings,
        clock: Callable[[], datetime] | None = None,
    ):
        self._session_service = session_service
        self._config = config
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def analyze(self, measurement: Spo2Measurement) -> Spo2AnalysisResponse:
        session = self._session_service.get_session(measurement.session_id)
        if session is None:
            return self._failure(measurement, "SESSION_NOT_FOUND")
        if session.user_id != measurement.user_id:
            return self._failure(measurement, "USER_MISMATCH")
        if session.device_id != measurement.device_id:
            return self._failure(measurement, "DEVICE_MISMATCH")
        if not self._session_is_active(session):
            return self._failure(measurement, "SESSION_EXPIRED")
        if not self._timestamp_is_valid(measurement.timestamp):
            return self._failure(measurement, "TIMESTAMP_OUTSIDE_TOLERANCE")
        if not self._spo2_is_valid(measurement.spo2):
            return self._failure(measurement, "SPO2_OUT_OF_RANGE")
        if measurement.measurement_source != "SYNTHETIC_SPO2_DEVICE":
            return self._failure(measurement, "MEASUREMENT_SOURCE_INVALID")
        if measurement.measurement_quality not in self._config.spo2_accepted_measurement_qualities:
            return self._failure(measurement, "MEASUREMENT_QUALITY_INVALID")

        status = self._status_for(measurement.spo2)
        return self._result(
            measurement,
            status=status,
            message=f"Synthetic SpO2 measurement accepted with engineering status {status}.",
            measurement_accepted=True,
        )

    def _session_is_active(self, session: BiometricSession) -> bool:
        return session.expires_at is not None and session.expires_at > self._clock()

    def _timestamp_is_valid(self, timestamp: datetime) -> bool:
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            return False
        return abs((timestamp - self._clock()).total_seconds()) <= self._config.timestamp_tolerance_seconds

    def _spo2_is_valid(self, spo2: float) -> bool:
        return self._config.spo2_min_value <= spo2 <= self._config.spo2_max_value

    def _status_for(self, spo2: float) -> str:
        if spo2 >= self._config.spo2_normal_threshold:
            return "NORMAL"
        if spo2 >= self._config.spo2_attention_threshold:
            return "ATTENTION_REQUIRED"
        if spo2 >= self._config.spo2_low_threshold:
            return "LOW"
        return "CRITICAL"

    @staticmethod
    def _result(
        measurement: Spo2Measurement,
        status: str,
        message: str,
        measurement_accepted: bool,
    ) -> Spo2AnalysisResponse:
        return Spo2AnalysisResponse(
            scenario=measurement.scenario,
            userId=measurement.user_id,
            sessionId=measurement.session_id,
            deviceId=measurement.device_id,
            spo2=measurement.spo2,
            timestamp=measurement.timestamp,
            measurementSource=measurement.measurement_source,
            measurementQuality=measurement.measurement_quality,
            status=status,
            healthStatus=f"SYNTHETIC_{status}",
            message=message,
            measurementAccepted=measurement_accepted,
        )

    @classmethod
    def _failure(cls, measurement: Spo2Measurement, reason: str) -> Spo2AnalysisResponse:
        return cls._result(
            measurement,
            status="INVALID",
            message=reason,
            measurement_accepted=False,
        )
