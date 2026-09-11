from fastapi import APIRouter

from app.schemas.liveness import BiometricSession, SessionCreateRequest
from app.services.biometric_service import BiometricSessionService

router = APIRouter(tags=["synthetic-biometric"])
session_service = BiometricSessionService()


@router.post("/api/ai/biometric/session", response_model=BiometricSession, status_code=201)
@router.post("/sessions", response_model=BiometricSession, status_code=201)
@router.post("/api/v1/biometric/sessions", response_model=BiometricSession, status_code=201)
def create_session(request: SessionCreateRequest) -> BiometricSession:
    return session_service.create_session(request.user_id, request.device_id)
