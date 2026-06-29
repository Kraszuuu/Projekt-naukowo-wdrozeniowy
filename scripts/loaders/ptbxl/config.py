from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "raw" / "ptb-xl"
OUTPUT_DIR = PROJECT_ROOT / "results" / "ptb-xl" / "etap2_verification"

DATABASE_CSV = DATA_DIR / "ptbxl_database.csv"
SCP_STATEMENTS_CSV = DATA_DIR / "scp_statements.csv"
SHA256SUMS_FILE = DATA_DIR / "SHA256SUMS.txt"
LICENSE_FILE = DATA_DIR / "LICENSE.txt"
RECORDS_FILE = DATA_DIR / "RECORDS"

LEAD_NAMES = ["I", "II", "III", "AVR", "AVL", "AVF", "V1", "V2", "V3", "V4", "V5", "V6"]

# Pięć nadklas diagnostycznych SCP-ECG używanych w projekcie.
SUPERCLASSES = ["NORM", "MI", "STTC", "CD", "HYP"]

# Sugerowany podział foldów (PTB-XL dostarcza strat_fold 1-10).
TRAIN_FOLDS = list(range(1, 9))   # 1-8
VAL_FOLD = 9
TEST_FOLD = 10

# Częstotliwości próbkowania dostępne w PTB-XL.
SAMPLING_RATE_LR = 100   # filename_lr, records100/
SAMPLING_RATE_HR = 500   # filename_hr, records500/

EXPECTED_LEADS = 12
EXPECTED_RECORDS = 21799   # liczba rekordów EKG w v1.0.3

# Oczekiwana treść licencji (CC BY 4.0).
LICENSE_EXPECTED_HEADER = "Creative Commons Attribution 4.0 International Public License"

# Pliki metadanych (nie-sygnałowe), które zawsze weryfikujemy w całości.
KEY_FILES = [
    "ptbxl_database.csv",
    "scp_statements.csv",
    "RECORDS",
    "LICENSE.txt",
    "example_physionet.py",
    "ptbxl_v102_changelog.txt",
    "ptbxl_v103_changelog.txt",
]
