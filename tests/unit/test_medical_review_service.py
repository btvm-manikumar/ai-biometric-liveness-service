"""Unit tests for the synthetic Task 3 medical-review service."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.medical_review import MedicalReviewCreationRequest, MedicalReviewDecisionRequest
from app.services.medical_review_service import MedicalReviewService
from app.synthetic.medical_review_generator import MedicalReviewGenerator


REVIEWER_ID = "SYNTH-REVIEWER-001"
NOW = datetime(2026, 9, 16, 12, 0, tzinfo=timezone.utc)


def create_service() -> MedicalReviewService:
	return MedicalReviewService()


def create_review(
	service: MedicalReviewService | None = None,
	scenario: str = "HIGH_RISK_CASE",
) -> tuple[MedicalReviewService, str]:
	service = service or create_service()
	result = MedicalReviewGenerator().generate_case(scenario)
	review = service.create_review_request(result)
	assert review is not None
	return service, review.review_id


def assign_review(service: MedicalReviewService, review_id: str) -> None:
	assigned = service.assign_reviewer(review_id, REVIEWER_ID)
	assert assigned.status == "IN_REVIEW"


def decision(review_id: str, value: str, comments: str | None = "Synthetic review comment."):
	return MedicalReviewDecisionRequest(
		reviewId=review_id,
		reviewerId=REVIEWER_ID,
		decision=value,
		reviewComments=comments,
		reviewedAt=NOW,
	)


def test_create_medical_review():
	service, review_id = create_review()

	review = service.get_review_request(review_id)

	assert review is not None
	assert review.status == "PENDING"
	assert review.review_id.startswith("SYNTH-REVIEW-")


def test_normal_case_does_not_unnecessarily_require_review():
	result = MedicalReviewGenerator().generate_normal_case()

	assert create_service().create_review_request(result) is None


def test_high_risk_case_creates_review():
	service, review_id = create_review(scenario="HIGH_RISK_CASE")

	assert service.get_review_request(review_id).risk_level == "HIGH_RISK"


def test_critical_case_creates_review():
	service, review_id = create_review(scenario="CRITICAL_CASE")

	assert service.get_review_request(review_id).risk_level == "CRITICAL"


def test_get_review():
	service, review_id = create_review()

	review = service.get_review_request(review_id)

	assert review is not None
	assert review.review_id == review_id


def test_assign_authorized_synthetic_reviewer():
	service, review_id = create_review()

	assigned = service.assign_reviewer(review_id, REVIEWER_ID)

	assert assigned.reviewer_id == REVIEWER_ID
	assert assigned.status == "IN_REVIEW"


def test_reject_unauthorized_reviewer():
	service, review_id = create_review()

	with pytest.raises(ValueError, match="authorized synthetic reviewer"):
		service.assign_reviewer(review_id, "SYNTH-REVIEWER-999")


def test_assignment_moves_review_to_in_review():
	service, review_id = create_review()

	assign_review(service, review_id)

	assert service.get_review_request(review_id).status == "IN_REVIEW"


def test_approve_decision():
	service, review_id = create_review()
	assign_review(service, review_id)

	result = service.submit_review_decision(decision(review_id, "APPROVE"))

	assert result.status == "APPROVED"
	assert result.decision == "APPROVE"


def test_reject_decision():
	service, review_id = create_review()
	assign_review(service, review_id)

	result = service.submit_review_decision(decision(review_id, "REJECT", "Synthetic risk rejected."))

	assert result.status == "REJECTED"
	assert result.decision == "REJECT"


def test_request_changes_decision():
	service, review_id = create_review()
	assign_review(service, review_id)

	result = service.submit_review_decision(decision(review_id, "REQUEST_CHANGES", "Synthetic clarification needed."))

	assert result.status == "CHANGES_REQUESTED"
	assert result.decision == "REQUEST_CHANGES"


def test_reject_without_comments_fails():
	service, review_id = create_review()
	assign_review(service, review_id)

	with pytest.raises(ValidationError, match="reviewComments"):
		decision(review_id, "REJECT", None)


def test_request_changes_without_comments_fails():
	service, review_id = create_review()
	assign_review(service, review_id)

	with pytest.raises(ValidationError, match="reviewComments"):
		decision(review_id, "REQUEST_CHANGES", None)


@pytest.mark.parametrize("risk_level", ["UNSUPPORTED", "NORMALIZED"])
def test_invalid_risk_level(risk_level: str):
	with pytest.raises(ValidationError):
		MedicalReviewCreationRequest.model_validate(
			MedicalReviewGenerator().generate_high_risk_case().model_dump() | {"risk_level": risk_level}
		)


def test_ai_confidence_below_zero():
	with pytest.raises(ValidationError):
		MedicalReviewCreationRequest.model_validate(
			MedicalReviewGenerator().generate_high_risk_case().model_dump() | {"ai_confidence": -1}
		)


def test_ai_confidence_above_100():
	with pytest.raises(ValidationError):
		MedicalReviewCreationRequest.model_validate(
			MedicalReviewGenerator().generate_high_risk_case().model_dump() | {"ai_confidence": 101}
		)


def test_invalid_decision():
	with pytest.raises(ValidationError):
		decision("SYNTH-REVIEW-001", "ESCALATE")


def test_medication_information_cannot_become_a_prescription():
	service, review_id = create_review(scenario="MEDICATION_INFORMATION_CASE")
	review = service.get_review_request(review_id)

	assert review.medicine_recommendation is not None
	assert "prescription" in review.medicine_recommendation.lower()
	assert not hasattr(review, "prescription")
	assert not hasattr(review, "medication_order")


def test_invalid_session():
	result = MedicalReviewGenerator().generate_high_risk_case().model_copy(
		update={"session_id": "REAL-SESSION-001"}
	)

	with pytest.raises(ValueError, match="synthetic session"):
		create_service().create_review_request(result)


def test_invalid_user():
	result = MedicalReviewGenerator().generate_high_risk_case().model_copy(
		update={"user_id": "REAL-USER-001"}
	)

	with pytest.raises(ValueError, match="synthetic user"):
		create_service().create_review_request(result)
