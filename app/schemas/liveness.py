from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict, Field


class SyntheticMeasurement(BaseModel):
    scenario: str = "UNLABELLED"
    user_id: str = Field(..., alias="userId", min_length=1)
    session_id: str = Field(..., alias="sessionId", min_length=1)
    device_id: str = Field(..., alias="deviceId", min_length=1)
    face_match_score: float = Field(..., alias="faceMatchScore")
    liveness_score: float = Field(..., alias="livenessScore")
    timestamp: datetime
    measurement_source: str = Field(..., alias="measurementSource")
    measurement_quality: str = Field(..., alias="measurementQuality")

    model_config = ConfigDict(populate_by_name=True)


class SessionCreateRequest(BaseModel):
    user_id: str = Field(..., alias="userId", min_length=1)
    device_id: str = Field(..., alias="deviceId", min_length=1)

    model_config = ConfigDict(populate_by_name=True)


class BiometricSession(BaseModel):
    user_id: str = Field(..., alias="userId")
    session_id: str = Field(..., alias="sessionId")
    device_id: str = Field(..., alias="deviceId")
    created_at: datetime | None = Field(default=None, alias="createdAt")
    expires_at: datetime | None = Field(default=None, alias="expiresAt")
    liveness_verified: bool = Field(default=False, alias="livenessVerified")
    authenticated: bool = True

    model_config = ConfigDict(populate_by_name=True)


class AuthenticationResult(BaseModel):
    authenticated: bool
    face_verified: bool = Field(..., alias="faceVerified")
    liveness_verified: bool = Field(..., alias="livenessVerified")
    status: str
    message: str
    user_id: str = Field(..., alias="userId")
    session_id: str = Field(..., alias="sessionId")
    device_id: str = Field(..., alias="deviceId")
    checks: List[str]
    failure_reason: str | None = Field(default=None, alias="failureReason")

    model_config = ConfigDict(populate_by_name=True)
