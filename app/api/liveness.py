from fastapi import APIRouter

from app.api.biometric import session_service
from app.config.settings import settings
from app.schemas.liveness import AuthenticationResult, SyntheticMeasurement
from app.services.liveness_service import LivenessVerificationService

router = APIRouter(tags=["synthetic-liveness"])
verification_service = LivenessVerificationService(session_service, settings)


@router.post("/api/ai/biometric/liveness", response_model=AuthenticationResult)
@router.post("/verify", response_model=AuthenticationResult)
@router.post("/api/v1/liveness/verify", response_model=AuthenticationResult)
def verify_liveness(measurement: SyntheticMeasurement) -> AuthenticationResult:
    return verification_service.verify(measurement)
