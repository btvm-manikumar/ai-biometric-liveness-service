import asyncio
import json
from pathlib import Path

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


def test_session_and_liveness_flow_accepts_synthetic_record():
    session_response = request(
        "POST",
        "/api/v1/biometric/sessions",
        json={"userId": "SYNTH-USER-001", "deviceId": "SYNTH-DEVICE-001"},
    )
    session_id = session_response.json()["sessionId"]
    created_at = session_response.json()["createdAt"]

    measurement = {
        "userId": "SYNTH-USER-001",
        "sessionId": session_id,
        "deviceId": "SYNTH-DEVICE-001",
        "faceMatchScore": 0.94,
        "livenessScore": 0.91,
        "timestamp": created_at,
        "measurementSource": "SYNTHETIC_CAMERA",
        "measurementQuality": "GOOD",
    }
    response = request("POST", "/api/v1/liveness/verify", json=measurement)

    assert response.status_code == 200
    assert response.json()["authenticated"] is True


def test_task_one_api_paths_accept_synthetic_json():
    session_response = request(
        "POST",
        "/api/ai/biometric/session",
        json={"userId": "SYNTH-USER-001", "deviceId": "SYNTH-DEVICE-001"},
    )
    session = session_response.json()
    response = request(
        "POST",
        "/api/ai/biometric/liveness",
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

    result = response.json()
    assert session_response.status_code == 201
    assert response.status_code == 200
    assert result["authenticated"] is True
    assert result["faceVerified"] is True
    assert result["livenessVerified"] is True
    assert result["status"] == "VERIFIED"


def test_liveness_api_rejects_measurement_for_another_session():
    request(
        "POST",
        "/api/v1/biometric/sessions",
        json={"userId": "SYNTH-USER-001", "deviceId": "SYNTH-DEVICE-001"},
    )
    measurement = {
        "userId": "SYNTH-USER-001",
        "sessionId": "SYNTH-SESSION-NOT-REGISTERED",
        "deviceId": "SYNTH-DEVICE-001",
        "faceMatchScore": 0.94,
        "livenessScore": 0.91,
        "timestamp": "2026-09-11T19:30:00Z",
        "measurementSource": "SYNTHETIC_CAMERA",
        "measurementQuality": "GOOD",
    }

    response = request("POST", "/api/v1/liveness/verify", json=measurement)

    assert response.status_code == 200
    assert response.json()["failureReason"] == "SESSION_NOT_FOUND"


def test_every_dataset_record_through_liveness_api():
    records = json.loads(
        (Path(__file__).parents[2] / "data" / "synthetic_liveness_data.json").read_text(encoding="utf-8")
    )

    for record in records:
        session_response = request(
            "POST",
            "/api/ai/biometric/session",
            json={"userId": record["userId"], "deviceId": record["deviceId"]},
        )
        session = session_response.json()
        measurement = {**record, "sessionId": session["sessionId"], "timestamp": session["createdAt"]}
        response = request("POST", "/api/ai/biometric/liveness", json=measurement)
        result = response.json()

        assert response.status_code == 200
        if record["scenario"] == "VALID":
            assert result["faceVerified"] is True
            assert result["livenessVerified"] is True
            assert result["authenticated"] is True
        elif record["scenario"] == "FACE_FAILURE":
            assert result["faceVerified"] is False
            assert result["authenticated"] is False
        elif record["scenario"] == "LIVENESS_FAILURE":
            assert result["livenessVerified"] is False
            assert result["authenticated"] is False
        elif record["scenario"] == "BOTH_FAILURE":
            assert result["faceVerified"] is False
            assert result["livenessVerified"] is False
            assert result["authenticated"] is False
        else:
            assert result["status"] == "FAILED"
            assert result["failureReason"] == "FACE_SCORE_OUT_OF_RANGE"
