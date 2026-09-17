"""Integration tests for the synthetic Task 3 medical-review API."""

import asyncio

import httpx

from app.api.biometric import session_service
from app.api.medical_review import medical_review_service
from app.main import app


REVIEWER_ID = "SYNTH-REVIEWER-001"
REVIEW_TIMESTAMP = "2026-09-16T12:00:00Z"


def request(method: str, path: str, **kwargs):
	async def send():
		transport = httpx.ASGITransport(app=app)
		async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
			return await client.request(method, path, **kwargs)

	return asyncio.run(send())


def setup_function():
	session_service.clear()
	medical_review_service.clear()


def create_session(device_id: str = "SYNTH-DEVICE-001") -> dict:
	response = request(
		"POST",
		"/api/v1/biometric/sessions",
		json={"userId": "SYNTH-USER-001", "deviceId": device_id},
	)
	assert response.status_code == 201
	return response.json()


def create_review() -> dict:
	response = request(
		"POST",
		"/api/v1/medical-review",
		json={
			"sessionId": "SYNTH-SESSION-001",
			"userId": "SYNTH-USER-001",
			"riskLevel": "HIGH_RISK",
			"aiConfidence": 84,
			"recommendationType": "MEDICAL_REVIEW",
			"medicineRecommendation": None,
			"doctorReviewRequired": True,
			"aiRecommendation": "Synthetic medical review required.",
		},
	)
	assert response.status_code == 200
	return response.json()


def assign_review(review_id: str) -> dict:
	response = request(
		"POST",
		f"/api/v1/medical-review/{review_id}/assign",
		json={"reviewerId": REVIEWER_ID},
	)
	assert response.status_code == 200
	return response.json()


def test_health_endpoint_works():
	response = request("GET", "/health")

	assert response.status_code == 200
	assert response.json() == {"status": "ok", "dataMode": "synthetic-only"}


def test_task_one_session_endpoint_still_works():
	response = request(
		"POST",
		"/api/v1/biometric/sessions",
		json={"userId": "SYNTH-USER-001", "deviceId": "SYNTH-DEVICE-001"},
	)

	assert response.status_code == 201
	assert response.json()["userId"] == "SYNTH-USER-001"


def test_task_one_liveness_endpoint_still_works():
	session = create_session()
	response = request(
		"POST",
		"/api/v1/liveness/verify",
		json={
			"userId": "SYNTH-USER-001",
			"sessionId": session["sessionId"],
			"deviceId": "SYNTH-DEVICE-001",
			"faceMatchScore": 0.94,
			"livenessScore": 0.91,
			"timestamp": session["createdAt"],
			"measurementSource": "SYNTHETIC_CAMERA",
			"measurementQuality": "GOOD",
		},
	)

	assert response.status_code == 200
	assert response.json()["authenticated"] is True


def test_task_two_spo2_endpoint_still_works():
	session = create_session(device_id="SYNTH-SPO2-DEVICE-001")
	response = request(
		"POST",
		"/api/v1/spo2",
		json={
			"userId": "SYNTH-USER-001",
			"sessionId": session["sessionId"],
			"deviceId": "SYNTH-SPO2-DEVICE-001",
			"spo2": 98,
			"timestamp": session["createdAt"],
			"measurementSource": "SYNTHETIC_SPO2_DEVICE",
			"measurementQuality": "GOOD",
		},
	)

	assert response.status_code == 200
	assert response.json()["status"] == "NORMAL"
	assert response.json()["measurementAccepted"] is True


def test_create_and_get_synthetic_medical_review():
	review = create_review()

	response = request("GET", f"/api/v1/medical-review/{review['reviewId']}")

	assert response.status_code == 200
	assert response.json()["status"] == "PENDING"
	assert response.json()["reviewId"] == review["reviewId"]


def test_assign_synthetic_reviewer_and_submit_approve_decision():
	review = create_review()

	assigned = assign_review(review["reviewId"])
	decision = request(
		"POST",
		f"/api/v1/medical-review/{review['reviewId']}/decision",
		json={
			"reviewerId": REVIEWER_ID,
			"decision": "APPROVE",
			"reviewComments": "Synthetic review approved for demonstration.",
			"reviewedAt": REVIEW_TIMESTAMP,
		},
	)

	assert assigned["status"] == "IN_REVIEW"
	assert decision.status_code == 200
	assert decision.json()["status"] == "APPROVED"


def test_reject_workflow():
	review = create_review()
	assign_review(review["reviewId"])

	response = request(
		"POST",
		f"/api/v1/medical-review/{review['reviewId']}/decision",
		json={
			"reviewerId": REVIEWER_ID,
			"decision": "REJECT",
			"reviewComments": "Synthetic review rejected for demonstration.",
			"reviewedAt": REVIEW_TIMESTAMP,
		},
	)

	assert response.status_code == 200
	assert response.json()["status"] == "REJECTED"


def test_request_changes_workflow():
	review = create_review()
	assign_review(review["reviewId"])

	response = request(
		"POST",
		f"/api/v1/medical-review/{review['reviewId']}/decision",
		json={
			"reviewerId": REVIEWER_ID,
			"decision": "REQUEST_CHANGES",
			"reviewComments": "Synthetic clarification is required.",
			"reviewedAt": REVIEW_TIMESTAMP,
		},
	)

	assert response.status_code == 200
	assert response.json()["status"] == "CHANGES_REQUESTED"


def test_unauthorized_reviewer_is_rejected():
	review = create_review()

	response = request(
		"POST",
		f"/api/v1/medical-review/{review['reviewId']}/assign",
		json={"reviewerId": "SYNTH-REVIEWER-999"},
	)

	assert response.status_code == 400
	assert "authorized" in response.json()["detail"]


def test_invalid_decision_is_rejected():
	review = create_review()
	assign_review(review["reviewId"])

	response = request(
		"POST",
		f"/api/v1/medical-review/{review['reviewId']}/decision",
		json={
			"reviewerId": REVIEWER_ID,
			"decision": "ESCALATE",
			"reviewedAt": REVIEW_TIMESTAMP,
		},
	)

	assert response.status_code == 422


def test_missing_review_comments_is_rejected():
	review = create_review()
	assign_review(review["reviewId"])

	response = request(
		"POST",
		f"/api/v1/medical-review/{review['reviewId']}/decision",
		json={
			"reviewerId": REVIEWER_ID,
			"decision": "REJECT",
			"reviewedAt": REVIEW_TIMESTAMP,
		},
	)

	assert response.status_code == 422
