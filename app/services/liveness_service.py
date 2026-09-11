from datetime import datetime, timezone
from typing import Callable

from app.config.settings import Settings
from app.schemas.liveness import AuthenticationResult, SyntheticMeasurement
from app.services.biometric_service import BiometricSessionService


class LivenessVerificationService:
    def __init__(
        self,
        session_service: BiometricSessionService,
        config: Settings,
        clock: Callable[[], datetime] | None = None,
    ):
        self._session_service = session_service
        self._config = config
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def verify(self, measurement: SyntheticMeasurement) -> AuthenticationResult:
        session = self._session_service.get_session(measurement.session_id)
        checks = ["face_verification", "liveness_verification", "device_verification", "session_verification"]
        face_verified = 0 <= measurement.face_match_score <= 1 and (
            measurement.face_match_score >= self._config.face_match_threshold
        )
        liveness_verified = 0 <= measurement.liveness_score <= 1 and (
            measurement.liveness_score >= self._config.liveness_threshold
        )

        if session is None:
            return self._failure(measurement, checks, "SESSION_NOT_FOUND", face_verified, liveness_verified)
        if session.user_id != measurement.user_id:
            return self._failure(measurement, checks, "USER_MISMATCH", face_verified, liveness_verified)
        if session.device_id != measurement.device_id:
            return self._failure(measurement, checks, "DEVICE_MISMATCH", face_verified, liveness_verified)

        now = self._clock()
        if session.expires_at is None or session.expires_at <= now:
            return self._failure(measurement, checks, "SESSION_EXPIRED", face_verified, liveness_verified)
        if measurement.timestamp.tzinfo is None or abs((measurement.timestamp - now).total_seconds()) > self._config.timestamp_tolerance_seconds:
            return self._failure(measurement, checks, "TIMESTAMP_OUTSIDE_TOLERANCE", face_verified, liveness_verified)
        if not 0 <= measurement.face_match_score <= 1:
            return self._failure(measurement, checks, "FACE_SCORE_OUT_OF_RANGE", face_verified, liveness_verified)
        if not 0 <= measurement.liveness_score <= 1:
            return self._failure(measurement, checks, "LIVENESS_SCORE_OUT_OF_RANGE", face_verified, liveness_verified)
        if not measurement.measurement_source:
            return self._failure(measurement, checks, "MEASUREMENT_SOURCE_MISSING", face_verified, liveness_verified)
        if not measurement.measurement_quality:
            return self._failure(measurement, checks, "MEASUREMENT_QUALITY_MISSING", face_verified, liveness_verified)
        if not face_verified:
            return self._failure(measurement, checks, "FACE_MATCH_BELOW_THRESHOLD", face_verified, liveness_verified)
        if not liveness_verified:
            return self._failure(measurement, checks, "LIVENESS_BELOW_THRESHOLD", face_verified, liveness_verified)

        session.liveness_verified = True
        return AuthenticationResult(
            authenticated=True,
            faceVerified=True,
            livenessVerified=True,
            status="VERIFIED",
            message="Synthetic biometric and liveness verification succeeded.",
            userId=measurement.user_id,
            sessionId=measurement.session_id,
            deviceId=measurement.device_id,
            checks=checks,
        )

    @staticmethod
    def _failure(measurement, checks, reason, face_verified, liveness_verified):
        return AuthenticationResult(
            authenticated=False,
            faceVerified=face_verified,
            livenessVerified=liveness_verified,
            status="FAILED",
            message=reason,
            userId=measurement.user_id,
            sessionId=measurement.session_id,
            deviceId=measurement.device_id,
            checks=checks,
            failureReason=reason,
        )
