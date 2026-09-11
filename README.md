<<<<<<< HEAD
# AI Model 02: Synthetic Biometric and Liveness Health Verification

Task 1 implements a synthetic-only face and liveness authentication flow. It verifies that a synthetic measurement belongs to the registered synthetic user, device, and session before returning an authentication result.

## Synthetic-data boundary

This project uses synthetic identifiers, scores, timestamps, and measurement metadata only. It does not accept, store, or process real people's biometric data, face images, camera input, patient data, health data, external biometric providers, facial recognition services, or real liveness detection.

## Architecture

```text
Synthetic user and device
	|
	v
Biometric session service (in-memory registry)
	|
	v
Synthetic face score check
	|
	v
Synthetic liveness score check
	|
	v
Device and session identity checks
	|
	v
Authentication result
```

- `app/synthetic/data_generator.py` creates deterministic records using `SYNTH-*` identifiers.
- `app/services/biometric_service.py` registers synthetic sessions in memory.
- `app/services/liveness_service.py` applies source, quality, identity, and configurable score checks.
- `app/schemas/liveness.py` defines the Pydantic request and response contracts while exposing the required camelCase JSON fields.
- `app/api/biometric.py` and `app/api/liveness.py` expose the session and verification APIs.

The default engineering/test configuration is a `0.80` face-match threshold, a `0.80` liveness threshold, a 10-minute session expiry, and a 300-second timestamp tolerance. These are synthetic-data test settings, not clinical thresholds or medically validated values. The values can be overridden with `FACE_MATCH_THRESHOLD`, `LIVENESS_THRESHOLD`, `SESSION_EXPIRY_MINUTES`, and `TIMESTAMP_TOLERANCE_SECONDS`.

## Setup

Python 3.11 or newer is required.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Run the API:

```powershell
uvicorn app.main:app --reload
```

The health endpoint is available at `http://127.0.0.1:8000/health` and reports `dataMode: synthetic-only`.

## API flow

Create a synthetic session:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/v1/biometric/sessions `
  -ContentType "application/json" `
  -Body '{"userId":"SYNTH-USER-001","deviceId":"SYNTH-DEVICE-001"}'
```

Submit a synthetic liveness measurement using the returned `sessionId`:

```json
{
  "userId": "SYNTH-USER-001",
	"sessionId": "REPLACE_WITH_RETURNED_SESSION_ID",
  "deviceId": "SYNTH-DEVICE-001",
  "faceMatchScore": 0.94,
  "livenessScore": 0.91,
  "timestamp": "2026-09-11T19:30:00Z",
  "measurementSource": "SYNTHETIC_CAMERA",
  "measurementQuality": "GOOD"
}
```

POST that payload to `/api/v1/liveness/verify`. The result is authenticated only when the session exists, user and device IDs match, the source and quality are accepted, and both scores meet their thresholds.

## Tests

The tests use only in-memory services and synthetic records:

```powershell
pytest -q
```

The dataset in `data/synthetic_liveness_data.json` contains exactly 100 labelled synthetic records: 25 `VALID`, 20 `FACE_FAILURE`, 20 `LIVENESS_FAILURE`, 15 `BOTH_FAILURE`, and 20 `INVALID`. It is not biometric or health data.

## Deliberately excluded

SpO2, medical review, measurement history, API authentication/security, real face recognition, and real liveness detection are outside Task 1.
=======
# ai-biometric-liveness-service
>>>>>>> bf3bfce9569c5cd82477a728d1c8c9cad8a3652b
