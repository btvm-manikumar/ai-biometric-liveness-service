"""Unit tests for the synthetic Task 3 medical-review dataset."""

import json
from collections import Counter
from pathlib import Path


DATASET_PATH = Path(__file__).parents[2] / "data" / "synthetic_medical_review_data.json"
REQUIRED_FIELDS = {
	"scenario",
	"sessionId",
	"userId",
	"riskLevel",
	"aiConfidence",
	"recommendationType",
	"medicineRecommendation",
	"doctorReviewRequired",
	"aiRecommendation",
}
EXPECTED_COUNTS = {
	"NORMAL_CASE": 20,
	"ATTENTION_CASE": 20,
	"HIGH_RISK_CASE": 20,
	"CRITICAL_CASE": 20,
	"MEDICAL_REVIEW_CASE": 10,
	"MEDICATION_INFORMATION_CASE": 10,
}


def load_records() -> list[dict]:
	return json.loads(DATASET_PATH.read_text(encoding="utf-8"))


def test_synthetic_medical_review_dataset_has_exact_distribution():
	records = load_records()

	assert len(records) == 100
	assert Counter(record["scenario"] for record in records) == Counter(EXPECTED_COUNTS)


def test_every_record_contains_required_fields():
	records = load_records()

	assert all(REQUIRED_FIELDS <= record.keys() for record in records)


def test_all_identifiers_are_synthetic():
	records = load_records()

	identifier_fields = {"sessionId", "userId", "reviewerId"}
	for record in records:
		for field in identifier_fields & record.keys():
			assert isinstance(record[field], str)
			assert record[field].startswith("SYNTH-")


def test_dataset_contains_no_prescriptions_or_medication_orders():
	records = load_records()

	forbidden_fields = {"prescription", "prescriptionOrder", "medicationOrder", "medication_order"}
	assert all(forbidden_fields.isdisjoint(record.keys()) for record in records)
	assert all(
		record["medicineRecommendation"] is None
		or "informational" in record["medicineRecommendation"].lower()
		or "not a prescription" in record["medicineRecommendation"].lower()
		for record in records
	)
