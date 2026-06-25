from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "raw" / "incart" / "files"
OUTPUT_DIR = PROJECT_ROOT / "data"

RECORDS_FILE = DATA_DIR / "RECORDS"
PATIENT_DIAGNOSES_FILE = DATA_DIR / "files-patients-diagnoses.txt"
RECORD_DESCRIPTIONS_FILE = DATA_DIR / "record-descriptions.txt"

LEAD_NAMES = ["I", "II", "III", "AVR", "AVL", "AVF", "V1", "V2", "V3", "V4", "V5", "V6"]
EXPECTED_FS = 257
EXPECTED_SAMPLES = 462600
EXPECTED_LEADS = 12

SIGNAL_PARTITION_DIR = OUTPUT_DIR / "processed" / "incart" / "signals"
ANNOTATION_PARTITION_DIR = OUTPUT_DIR / "processed" / "incart" / "annotations"

# Per-record sample limit (None = full 462600 samples / 30 min).
# 5000 samples ≈ 19.5 s @ 257 Hz ≈ 100× reduction.
MAX_SAMPLES = 417
