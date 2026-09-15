"""SpO2 API routes for Task 2."""

from fastapi import APIRouter

from app.api.biometric import session_service
from app.config.settings import settings
from app.schemas.spo2 import Spo2AnalysisResponse, Spo2Measurement
from app.services.spo2_service import Spo2Service

router = APIRouter(tags=["synthetic-spo2"])
spo2_service = Spo2Service(session_service, settings)


@router.post("/api/v1/spo2", response_model=Spo2AnalysisResponse)
def analyze_spo2(measurement: Spo2Measurement) -> Spo2AnalysisResponse:
	return spo2_service.analyze(measurement)
