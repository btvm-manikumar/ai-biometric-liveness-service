"""Thin API routes for the synthetic Task 3 medical-review workflow."""

from fastapi import APIRouter, HTTPException

from app.schemas.medical_review import (
	MedicalReviewAssignmentRequest,
	MedicalReviewCreationRequest,
	MedicalReviewDecisionPayload,
	MedicalReviewDecisionRequest,
	MedicalReviewResponse,
)
from app.services.medical_review_service import MedicalReviewService


router = APIRouter(prefix="/api/v1/medical-review", tags=["synthetic-medical-review"])
medical_review_service = MedicalReviewService()


@router.post("", response_model=MedicalReviewResponse | None)
def create_medical_review(request: MedicalReviewCreationRequest) -> MedicalReviewResponse | None:
	try:
		return medical_review_service.create_review_request(request)
	except ValueError as error:
		raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/{review_id}", response_model=MedicalReviewResponse)
def get_medical_review(review_id: str) -> MedicalReviewResponse:
	review = medical_review_service.get_review_request(review_id)
	if review is None:
		raise HTTPException(status_code=404, detail="Medical review request not found")
	return review


@router.post("/{review_id}/assign", response_model=MedicalReviewResponse)
def assign_medical_reviewer(
	review_id: str,
	request: MedicalReviewAssignmentRequest,
) -> MedicalReviewResponse:
	try:
		return medical_review_service.assign_reviewer(review_id, request.reviewer_id)
	except ValueError as error:
		status_code = 404 if str(error) == "Medical review request not found" else 400
		raise HTTPException(status_code=status_code, detail=str(error)) from error


@router.post("/{review_id}/decision", response_model=MedicalReviewResponse)
def submit_medical_review_decision(
	review_id: str,
	request: MedicalReviewDecisionPayload,
) -> MedicalReviewResponse:
	try:
		decision = MedicalReviewDecisionRequest(
			reviewId=review_id,
			**request.model_dump(by_alias=True),
		)
		return medical_review_service.submit_review_decision(decision)
	except ValueError as error:
		status_code = 404 if str(error) == "Medical review request not found" else 400
		raise HTTPException(status_code=status_code, detail=str(error)) from error
