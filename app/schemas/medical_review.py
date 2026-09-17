"""Pydantic contracts for the synthetic Task 3 medical-review workflow."""

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator, model_validator


RiskLevel = Literal["NORMAL", "ATTENTION_REQUIRED", "HIGH_RISK", "CRITICAL"]
RecommendationType = Literal["LIFESTYLE_MONITORING", "MEDICAL_FOLLOW_UP", "MEDICAL_REVIEW"]
ReviewDecision = Literal["APPROVE", "REJECT", "REQUEST_CHANGES"]
ReviewStatus = Literal[
	"PENDING",
	"IN_REVIEW",
	"APPROVED",
	"REJECTED",
	"CHANGES_REQUESTED",
	"COMPLETED",
]


class MedicalReviewCreationRequest(BaseModel):
	"""Synthetic AI result submitted for medical-review evaluation."""

	scenario: str = Field(default="UNLABELLED", min_length=1)
	session_id: str = Field(..., alias="sessionId", min_length=1)
	user_id: str = Field(..., alias="userId", min_length=1)
	risk_level: RiskLevel = Field(..., alias="riskLevel")
	ai_confidence: float = Field(..., alias="aiConfidence", ge=0, le=100)
	recommendation_type: RecommendationType = Field(..., alias="recommendationType")
	medicine_recommendation: str | None = Field(default=None, alias="medicineRecommendation")
	doctor_review_required: StrictBool = Field(..., alias="doctorReviewRequired")
	ai_recommendation: str = Field(..., alias="aiRecommendation", min_length=1)
	created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), alias="createdAt")

	model_config = ConfigDict(populate_by_name=True, extra="forbid")

	@field_validator("ai_confidence", mode="before")
	@classmethod
	def validate_numeric_confidence(cls, value: object) -> object:
		if isinstance(value, bool) or not isinstance(value, (int, float)):
			raise ValueError("aiConfidence must be numeric")
		return value

	@field_validator("created_at")
	@classmethod
	def validate_timezone_aware_created_at(cls, value: datetime) -> datetime:
		if value.tzinfo is None or value.utcoffset() is None:
			raise ValueError("createdAt must be timezone-aware")
		return value


class MedicalReviewDecisionPayload(BaseModel):
	"""Decision body submitted by an authorized synthetic reviewer."""

	reviewer_id: str = Field(..., alias="reviewerId", min_length=1)
	decision: ReviewDecision
	review_comments: str | None = Field(default=None, alias="reviewComments")
	reviewed_at: datetime = Field(..., alias="reviewedAt")

	model_config = ConfigDict(populate_by_name=True, extra="forbid")

	@model_validator(mode="after")
	def validate_comments_for_non_approval(self):
		if self.decision in {"REJECT", "REQUEST_CHANGES"} and not self.review_comments:
			raise ValueError("reviewComments is required for REJECT or REQUEST_CHANGES")
		return self

	@field_validator("reviewed_at")
	@classmethod
	def validate_timezone_aware_reviewed_at(cls, value: datetime) -> datetime:
		if value.tzinfo is None or value.utcoffset() is None:
			raise ValueError("reviewedAt must be timezone-aware")
		return value


class MedicalReviewDecisionRequest(MedicalReviewDecisionPayload):
	"""Decision submitted to the service with its review identifier."""

	review_id: str = Field(..., alias="reviewId", min_length=1)


class MedicalReviewAssignmentRequest(BaseModel):
	"""Synthetic reviewer assignment submitted to the API."""

	reviewer_id: str = Field(..., alias="reviewerId", min_length=1)

	model_config = ConfigDict(populate_by_name=True, extra="forbid")


class MedicalReviewResponse(MedicalReviewCreationRequest):
	"""Synthetic medical-review record returned by the API."""

	review_id: str = Field(..., alias="reviewId", min_length=1)
	status: ReviewStatus
	reviewer_id: str | None = Field(default=None, alias="reviewerId")
	decision: ReviewDecision | None = None
	review_comments: str | None = Field(default=None, alias="reviewComments")
	reviewed_at: datetime | None = Field(default=None, alias="reviewedAt")

	model_config = ConfigDict(populate_by_name=True, extra="forbid")
