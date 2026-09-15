import asyncio

import httpx

from app.api.biometric import session_service
from app.main import app


def request(method: str, path: str, **kwargs):
	async def send():
		transport = httpx.ASGITransport(app=app)
		async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
			return await client.request(method, path, **kwargs)

	return asyncio.run(send())


def setup_function():
	session_service.clear()


def create_session(user_id: str = "SYNTH-USER-001", device_id: str = "SYNTH-SPO2-DEVICE-001") -> dict:
	response = request(
		"POST",
		"/api/v1/biometric/sessions",
		json={"userId": user_id, "deviceId": device_id},
	)
	assert response.status_code == 201
	return response.json()


def spo2_payload(session: dict) -> dict:
	return {
		"userId": "SYNTH-USER-001",
		"sessionId": session["sessionId"],
		"deviceId": "SYNTH-SPO2-DEVICE-001",
		"spo2": 98,
		"timestamp": session["createdAt"],
		"measurementSource": "SYNTHETIC_SPO2_DEVICE",
		"measurementQuality": "GOOD",
	}


def test_health_endpoint_still_works():
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
	session = create_session(device_id="SYNTH-DEVICE-001")
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


def test_spo2_endpoint_accepts_valid_synthetic_measurement():
	session = create_session()

	response = request("POST", "/api/v1/spo2", json=spo2_payload(session))

	assert response.status_code == 200
	assert response.json()["status"] == "NORMAL"
	assert response.json()["measurementAccepted"] is True


def test_spo2_endpoint_rejects_invalid_spo2():
	session = create_session()
	payload = {**spo2_payload(session), "spo2": 101}

	response = request("POST", "/api/v1/spo2", json=payload)

	assert response.status_code == 200
	assert response.json()["status"] == "INVALID"
	assert response.json()["message"] == "SPO2_OUT_OF_RANGE"
	assert response.json()["measurementAccepted"] is False


def test_spo2_endpoint_rejects_wrong_user():
	session = create_session()
	payload = {**spo2_payload(session), "userId": "SYNTH-USER-999"}

	response = request("POST", "/api/v1/spo2", json=payload)

	assert response.status_code == 200
	assert response.json()["message"] == "USER_MISMATCH"
	assert response.json()["measurementAccepted"] is False


def test_spo2_endpoint_rejects_wrong_device():
	session = create_session()
	payload = {**spo2_payload(session), "deviceId": "SYNTH-SPO2-DEVICE-999"}

	response = request("POST", "/api/v1/spo2", json=payload)

	assert response.status_code == 200
	assert response.json()["message"] == "DEVICE_MISMATCH"
	assert response.json()["measurementAccepted"] is False


def test_spo2_endpoint_rejects_invalid_timestamp():
	session = create_session()
	payload = {**spo2_payload(session), "timestamp": "2026-09-15T16:00:00"}

	response = request("POST", "/api/v1/spo2", json=payload)

	assert response.status_code == 422
