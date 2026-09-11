import os


class Settings:
    app_name = os.getenv("APP_NAME", "Synthetic Biometric and Liveness Health Verification")
    # Engineering/test configuration for synthetic verification only.
    face_match_threshold = float(os.getenv("FACE_MATCH_THRESHOLD", "0.80"))
    liveness_threshold = float(os.getenv("LIVENESS_THRESHOLD", "0.80"))
    session_expiry_minutes = int(os.getenv("SESSION_EXPIRY_MINUTES", "10"))
    timestamp_tolerance_seconds = int(os.getenv("TIMESTAMP_TOLERANCE_SECONDS", "300"))
    accepted_measurement_source = os.getenv("ACCEPTED_MEASUREMENT_SOURCE", "SYNTHETIC_CAMERA")
    accepted_measurement_quality = os.getenv("ACCEPTED_MEASUREMENT_QUALITY", "GOOD")


settings = Settings()
