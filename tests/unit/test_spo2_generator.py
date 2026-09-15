import json
from collections import Counter
from datetime import datetime
from pathlib import Path


DATASET_PATH = Path(__file__).parents[2] / "data" / "synthetic_spo2_data.json"
REQUIRED_FIELDS = {
	"scenario",
	"userId",
	"sessionId",
	"deviceId",
	"spo2",
	"timestamp",
	"measurementSource",
	"measurementQuality",
}


def load_records() -> list[dict]:
	return json.loads(DATASET_PATH.read_text(encoding="utf-8"))


def test_synthetic_spo2_dataset_has_exact_scenario_distribution():
	records = load_records()

	assert len(records) == 100
	assert Counter(record["scenario"] for record in records) == Counter(
		{
			"NORMAL": 25,
			"ATTENTION": 20,
			"LOW": 20,
			"CRITICAL": 15,
			"INVALID": 20,
		}
	)


def test_every_spo2_record_has_required_synthetic_fields():
	records = load_records()

	assert all(REQUIRED_FIELDS <= record.keys() for record in records)
	assert all(record["userId"].startswith("SYNTH-") for record in records)
	assert all(record["sessionId"].startswith("SYNTH-") for record in records)
	assert all(record["deviceId"].startswith("SYNTH-") for record in records)
	assert all(record["measurementSource"] == "SYNTHETIC_SPO2_DEVICE" for record in records)
	assert all(
		datetime.fromisoformat(record["timestamp"].replace("Z", "+00:00")).tzinfo is not None
		for record in records
	)
