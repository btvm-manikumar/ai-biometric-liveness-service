from datetime import datetime, timezone
from collections import Counter
import json
from pathlib import Path

from app.synthetic.data_generator import SyntheticDataGenerator


def test_generator_is_deterministic_and_synthetic_only():
    timestamp = datetime(2026, 9, 11, 19, 30, tzinfo=timezone.utc)
    first = SyntheticDataGenerator(seed=7).create_measurement(timestamp=timestamp)
    second = SyntheticDataGenerator(seed=7).create_measurement(timestamp=timestamp)

    assert first == second
    assert first.user_id.startswith("SYNTH-")
    assert first.measurement_source == "SYNTHETIC_CAMERA"


def test_generator_creates_requested_dataset_size():
    records = SyntheticDataGenerator(seed=1).create_dataset(count=10)

    assert len(records) == 10
    assert [record.session_id for record in records] == [
        "SYNTH-SESSION-001",
        "SYNTH-SESSION-002",
        "SYNTH-SESSION-003",
        "SYNTH-SESSION-004",
        "SYNTH-SESSION-005",
        "SYNTH-SESSION-006",
        "SYNTH-SESSION-007",
        "SYNTH-SESSION-008",
        "SYNTH-SESSION-009",
        "SYNTH-SESSION-010",
    ]


def test_generator_cycles_through_all_synthetic_scenarios():
    records = SyntheticDataGenerator(seed=1).create_dataset(count=5)

    assert [record.scenario for record in records] == [
        "VALID",
        "FACE_FAILURE",
        "LIVENESS_FAILURE",
        "BOTH_FAILURE",
        "INVALID",
    ]
    assert all(record.measurement_source == "SYNTHETIC_CAMERA" for record in records)
    assert {record.measurement_quality for record in records} <= {"GOOD", "FAIR", "POOR"}


def test_checked_in_dataset_has_at_least_100_labelled_synthetic_records():
    dataset_path = Path(__file__).parents[2] / "data" / "synthetic_liveness_data.json"
    records = json.loads(dataset_path.read_text(encoding="utf-8"))

    assert len(records) == 100
    assert Counter(record["scenario"] for record in records) == Counter(
        {
            "VALID": 25,
            "FACE_FAILURE": 20,
            "LIVENESS_FAILURE": 20,
            "BOTH_FAILURE": 15,
            "INVALID": 20,
        }
    )
    assert all(record["userId"].startswith("SYNTH-") for record in records)
    assert all(record["measurementSource"] == "SYNTHETIC_CAMERA" for record in records)
