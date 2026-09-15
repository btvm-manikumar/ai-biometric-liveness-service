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
    spo2_normal_threshold = float(os.getenv("SPO2_NORMAL_THRESHOLD", "95"))
    spo2_attention_threshold = float(os.getenv("SPO2_ATTENTION_THRESHOLD", "90"))
    spo2_low_threshold = float(os.getenv("SPO2_LOW_THRESHOLD", "80"))
    spo2_min_value = float(os.getenv("SPO2_MIN_VALUE", "0"))
    spo2_max_value = float(os.getenv("SPO2_MAX_VALUE", "100"))
    spo2_accepted_measurement_qualities = tuple(
        quality.strip().upper()
        for quality in os.getenv("SPO2_ACCEPTED_MEASUREMENT_QUALITIES", "GOOD,FAIR,POOR").split(",")
        if quality.strip()
    )


settings = Settings()
