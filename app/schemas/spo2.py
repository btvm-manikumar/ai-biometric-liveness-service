"""Pydantic contracts for synthetic SpO2 measurements."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Spo2Measurement(BaseModel):
    """Synthetic SpO2 measurement submitted for analysis."""

    scenario: str = Field(default="UNLABELLED", min_length=1)
    user_id: str = Field(..., alias="userId", min_length=1)
    session_id: str = Field(..., alias="sessionId", min_length=1)
    device_id: str = Field(..., alias="deviceId", min_length=1)
    spo2: float
    timestamp: datetime
    measurement_source: Literal["SYNTHETIC_SPO2_DEVICE"] = Field(..., alias="measurementSource")
    measurement_quality: str = Field(..., alias="measurementQuality", min_length=1)

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("spo2", mode="before")
    @classmethod
    def validate_numeric_spo2(cls, value: object) -> object:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("spo2 must be numeric")
        return value

    @field_validator("timestamp")
    @classmethod
    def validate_timezone_aware_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must be timezone-aware")
        return value


class Spo2AnalysisResponse(Spo2Measurement):
    """Synthetic SpO2 analysis response envelope."""

    status: str
    health_status: str = Field(..., alias="healthStatus")
    message: str
    measurement_accepted: bool = Field(..., alias="measurementAccepted")
