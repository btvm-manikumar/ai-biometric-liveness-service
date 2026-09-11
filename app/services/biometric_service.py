from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.config.settings import Settings
from app.schemas.liveness import BiometricSession


class BiometricSessionService:
    """In-memory synthetic user, device, and session registry."""

    def __init__(self, config: Settings | None = None):
        self._sessions: dict[str, BiometricSession] = {}
        self._config = config or Settings()

    def create_session(self, user_id: str, device_id: str) -> BiometricSession:
        created_at = datetime.now(timezone.utc)
        session = BiometricSession(
            userId=user_id,
            sessionId=str(uuid4()),
            deviceId=device_id,
            createdAt=created_at,
            expiresAt=created_at + timedelta(minutes=self._config.session_expiry_minutes),
            livenessVerified=False,
            authenticated=True,
        )
        self._sessions[session.session_id] = session
        return session

    def register_synthetic_session(self, session: BiometricSession) -> BiometricSession:
        self._sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> BiometricSession | None:
        return self._sessions.get(session_id)

    def clear(self) -> None:
        self._sessions.clear()
