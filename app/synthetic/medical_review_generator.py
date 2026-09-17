"""Deterministic synthetic medical-review data generation for Task 3."""

from datetime import datetime, timezone
from typing import ClassVar

from app.schemas.medical_review import MedicalReviewCreationRequest


class MedicalReviewGenerator:
    """Creates fixed synthetic AI health-analysis cases for testing."""

    synthetic_reviewer_id: ClassVar[str] = "SYNTH-REVIEWER-001"
    _timestamp: ClassVar[datetime] = datetime(2026, 9, 16, 12, 0, tzinfo=timezone.utc)
    _scenarios: ClassVar[tuple[str, ...]] = (
        "NORMAL_CASE",
        "ATTENTION_CASE",
        "HIGH_RISK_CASE",
        "CRITICAL_CASE",
        "MEDICAL_REVIEW_CASE",
        "MEDICATION_INFORMATION_CASE",
    )

    def _create_case(
        self,
        scenario: str,
        risk_level: str,
        ai_confidence: float,
        recommendation_type: str,
        doctor_review_required: bool,
        ai_recommendation: str,
        medicine_recommendation: str | None = None,
    ) -> MedicalReviewCreationRequest:
        return MedicalReviewCreationRequest(
            scenario=scenario,
            sessionId="SYNTH-SESSION-001",
            userId="SYNTH-USER-001",
            riskLevel=risk_level,
            aiConfidence=ai_confidence,
            recommendationType=recommendation_type,
            medicineRecommendation=medicine_recommendation,
            doctorReviewRequired=doctor_review_required,
            aiRecommendation=f"[{scenario}] {ai_recommendation}",
            createdAt=self._timestamp,
        )

    def generate_normal_case(self) -> MedicalReviewCreationRequest:
        return self._create_case(
            "NORMAL_CASE",
            "NORMAL",
            98,
            "LIFESTYLE_MONITORING",
            False,
            "Continue synthetic wellness monitoring.",
        )

    def generate_attention_case(self) -> MedicalReviewCreationRequest:
        return self._create_case(
            "ATTENTION_CASE",
            "ATTENTION_REQUIRED",
            89,
            "MEDICAL_FOLLOW_UP",
            False,
            "Consider synthetic follow-up monitoring.",
        )

    def generate_high_risk_case(self) -> MedicalReviewCreationRequest:
        return self._create_case(
            "HIGH_RISK_CASE",
            "HIGH_RISK",
            84,
            "MEDICAL_REVIEW",
            True,
            "Authorized medical review is required.",
        )

    def generate_critical_case(self) -> MedicalReviewCreationRequest:
        return self._create_case(
            "CRITICAL_CASE",
            "CRITICAL",
            93,
            "MEDICAL_REVIEW",
            True,
            "Urgent authorized medical review is required.",
        )

    def generate_medical_review_case(self) -> MedicalReviewCreationRequest:
        return self._create_case(
            "MEDICAL_REVIEW_CASE",
            "HIGH_RISK",
            84,
            "MEDICAL_REVIEW",
            True,
            "The synthetic AI recommendation requires authorized medical review.",
        )

    def generate_medication_information_case(self) -> MedicalReviewCreationRequest:
        return self._create_case(
            "MEDICATION_INFORMATION_CASE",
            "HIGH_RISK",
            82,
            "MEDICAL_REVIEW",
            True,
            "Informational medication discussion requires authorized medical review.",
            medicine_recommendation="Synthetic informational medication topic only; not a prescription.",
        )

    def generate_case(self, scenario: str) -> MedicalReviewCreationRequest:
        generators = {
            "NORMAL_CASE": self.generate_normal_case,
            "ATTENTION_CASE": self.generate_attention_case,
            "HIGH_RISK_CASE": self.generate_high_risk_case,
            "CRITICAL_CASE": self.generate_critical_case,
            "MEDICAL_REVIEW_CASE": self.generate_medical_review_case,
            "MEDICATION_INFORMATION_CASE": self.generate_medication_information_case,
        }
        try:
            return generators[scenario]()
        except KeyError as error:
            raise ValueError(f"Unsupported synthetic medical-review scenario: {scenario}") from error

    def create_dataset(self, count: int = 6) -> list[MedicalReviewCreationRequest]:
        if count < 0:
            raise ValueError("count must be non-negative")
        return [self.generate_case(self._scenarios[index % len(self._scenarios)]) for index in range(count)]


_default_generator = MedicalReviewGenerator()


def generate_normal_case() -> MedicalReviewCreationRequest:
    return _default_generator.generate_normal_case()


def generate_attention_case() -> MedicalReviewCreationRequest:
    return _default_generator.generate_attention_case()


def generate_high_risk_case() -> MedicalReviewCreationRequest:
    return _default_generator.generate_high_risk_case()


def generate_critical_case() -> MedicalReviewCreationRequest:
    return _default_generator.generate_critical_case()


def generate_medical_review_case() -> MedicalReviewCreationRequest:
    return _default_generator.generate_medical_review_case()


def generate_medication_information_case() -> MedicalReviewCreationRequest:
    return _default_generator.generate_medication_information_case()
