"""In-memory synthetic medical-review workflow for Task 3."""

from collections.abc import Iterable
import re

from app.schemas.medical_review import (
    MedicalReviewCreationRequest,
    MedicalReviewDecisionRequest,
    MedicalReviewResponse,
)


class MedicalReviewService:
    """Stores and advances synthetic medical-review requests in memory."""

    _synthetic_session_pattern = re.compile(r"^SYNTH-SESSION-\d+$")
    _synthetic_user_pattern = re.compile(r"^SYNTH-USER-\d+$")
    _synthetic_reviewer_pattern = re.compile(r"^SYNTH-REVIEWER-\d+$")
    _authorized_reviewer_ids = {"SYNTH-REVIEWER-001"}

    def __init__(self, authorized_reviewer_ids: Iterable[str] | None = None):
        self._reviews: dict[str, MedicalReviewResponse] = {}
        self._next_review_number = 1
        if authorized_reviewer_ids is not None:
            self._authorized_reviewer_ids = set(authorized_reviewer_ids)

    def create_review_request(
        self,
        ai_result: MedicalReviewCreationRequest,
    ) -> MedicalReviewResponse | None:
        """Create a pending review only when the AI result requires review."""

        result = MedicalReviewCreationRequest.model_validate(ai_result)
        self._validate_ai_result(result)
        if not result.doctor_review_required:
            return None

        review_id = f"SYNTH-REVIEW-{self._next_review_number:03d}"
        self._next_review_number += 1
        review = MedicalReviewResponse(
            **result.model_dump(),
            reviewId=review_id,
            status="PENDING",
        )
        self._reviews[review_id] = review
        return review.model_copy(deep=True)

    def get_review_request(self, review_id: str) -> MedicalReviewResponse | None:
        """Return a stored synthetic review request, if it exists."""

        review = self._reviews.get(review_id)
        return review.model_copy(deep=True) if review is not None else None

    def assign_reviewer(self, review_id: str, reviewer_id: str) -> MedicalReviewResponse:
        """Assign an authorized synthetic reviewer and move the request in review."""

        review = self._get_required_review(review_id)
        self._validate_authorized_reviewer(reviewer_id)
        if review.status != "PENDING":
            raise ValueError("Only PENDING reviews can be assigned")

        updated = review.model_copy(update={"reviewer_id": reviewer_id, "status": "IN_REVIEW"})
        self._reviews[review_id] = updated
        return updated.model_copy(deep=True)

    def submit_review_decision(
        self,
        decision: MedicalReviewDecisionRequest,
    ) -> MedicalReviewResponse:
        """Store an authorized reviewer's decision."""

        submitted = MedicalReviewDecisionRequest.model_validate(decision)
        review = self._get_required_review(submitted.review_id)
        self._validate_authorized_reviewer(submitted.reviewer_id)
        if review.status != "IN_REVIEW":
            raise ValueError("Only IN_REVIEW requests can receive a decision")
        if review.reviewer_id != submitted.reviewer_id:
            raise ValueError("Decision reviewer does not match the assigned reviewer")
        if submitted.decision in {"REJECT", "REQUEST_CHANGES"} and not submitted.review_comments:
            raise ValueError("reviewComments is required for REJECT or REQUEST_CHANGES")

        status_by_decision = {
            "APPROVE": "APPROVED",
            "REJECT": "REJECTED",
            "REQUEST_CHANGES": "CHANGES_REQUESTED",
        }
        updated = review.model_copy(
            update={
                "status": status_by_decision[submitted.decision],
                "decision": submitted.decision,
                "review_comments": submitted.review_comments,
                "reviewed_at": submitted.reviewed_at,
            }
        )
        self._reviews[submitted.review_id] = updated
        return updated.model_copy(deep=True)

    def complete_review(self, review_id: str) -> MedicalReviewResponse:
        """Complete a review after an APPROVE or REJECT decision."""

        review = self._get_required_review(review_id)
        if review.status == "COMPLETED":
            return review.model_copy(deep=True)
        if review.status not in {"APPROVED", "REJECTED"}:
            raise ValueError("Only APPROVED or REJECTED reviews can be completed")

        updated = review.model_copy(update={"status": "COMPLETED"})
        self._reviews[review_id] = updated
        return updated.model_copy(deep=True)

    def clear(self) -> None:
        """Clear in-memory reviews for isolated tests."""

        self._reviews.clear()
        self._next_review_number = 1

    def _validate_ai_result(self, result: MedicalReviewCreationRequest) -> None:
        if not self._synthetic_session_pattern.fullmatch(result.session_id):
            raise ValueError("sessionId must identify an existing synthetic session")
        if not self._synthetic_user_pattern.fullmatch(result.user_id):
            raise ValueError("userId must identify an existing synthetic user")
        if not 0 <= result.ai_confidence <= 100:
            raise ValueError("aiConfidence must be between 0 and 100")

    def _validate_authorized_reviewer(self, reviewer_id: str) -> None:
        if not self._synthetic_reviewer_pattern.fullmatch(reviewer_id):
            raise ValueError("reviewerId must identify a synthetic reviewer")
        if reviewer_id not in self._authorized_reviewer_ids:
            raise ValueError("reviewerId is not an authorized synthetic reviewer")

    def _get_required_review(self, review_id: str) -> MedicalReviewResponse:
        review = self._reviews.get(review_id)
        if review is None:
            raise ValueError("Medical review request not found")
        return review
