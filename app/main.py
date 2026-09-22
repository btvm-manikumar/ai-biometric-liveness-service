from fastapi import FastAPI

from app.api.biometric import router as biometric_router
from app.api.liveness import router as liveness_router
from app.api.medical_review import router as medical_review_router
from app.api.spo2 import router as spo2_router
from app.config.settings import settings

app = FastAPI(title=settings.app_name, version="1.0.0")
app.include_router(biometric_router)
app.include_router(liveness_router)
app.include_router(medical_review_router)
app.include_router(spo2_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "dataMode": "synthetic-only"}
