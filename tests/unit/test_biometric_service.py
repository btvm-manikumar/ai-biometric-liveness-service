from datetime import timedelta, timezone
from uuid import UUID

from app.config.settings import Settings
from app.services.biometric_service import BiometricSessionService


def test_create_session_stores_synthetic_session_with_utc_expiry():
    config = Settings()
    service = BiometricSessionService(config)

    session = service.create_session("SYNTH-USER-001", "SYNTH-DEVICE-001")

    assert UUID(session.session_id)
    assert session.user_id == "SYNTH-USER-001"
    assert session.device_id == "SYNTH-DEVICE-001"
    assert session.liveness_verified is False
    assert session.created_at is not None
    assert session.expires_at is not None
    assert session.created_at.tzinfo == timezone.utc
    assert session.expires_at - session.created_at == timedelta(minutes=10)


def test_get_session_returns_stored_session_or_none():
    service = BiometricSessionService()
    created = service.create_session("SYNTH-USER-002", "SYNTH-DEVICE-002")

    assert service.get_session(created.session_id) == created
    assert service.get_session("missing-session") is None


def test_session_expiry_uses_injected_configuration():
    config = Settings()
    config.session_expiry_minutes = 3
    service = BiometricSessionService(config)

    session = service.create_session("SYNTH-USER-003", "SYNTH-DEVICE-003")

    assert session.expires_at - session.created_at == timedelta(minutes=3)