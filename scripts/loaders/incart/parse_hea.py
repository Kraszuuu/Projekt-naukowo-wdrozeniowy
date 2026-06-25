import re
import pandas as pd
from loaders.incart.config import (
    DATA_DIR, RECORDS_FILE, PATIENT_DIAGNOSES_FILE,
    RECORD_DESCRIPTIONS_FILE, LEAD_NAMES,
    EXPECTED_FS, EXPECTED_SAMPLES, EXPECTED_LEADS,
)


def get_record_ids():
    with open(RECORDS_FILE, "r") as f:
        return [line.strip() for line in f if line.strip()]


def parse_patient_diagnoses():
    with open(PATIENT_DIAGNOSES_FILE, "r") as f:
        lines = [line.strip() for line in f]

    result = {}
    i = 0
    while i < len(lines):
        patient_match = re.match(r"patient (\d+)", lines[i])
        if not patient_match:
            i += 1
            continue
        patient_id = int(patient_match.group(1))
        record_ids = lines[i + 1].split()
        diagnosis = lines[i + 2] if i + 2 < len(lines) else ""
        for rid in record_ids:
            result[rid] = {"patient_id": patient_id, "diagnosis": diagnosis}
        i += 3

    return result


def parse_record_descriptions():
    with open(RECORD_DESCRIPTIONS_FILE, "r") as f:
        lines = [line.strip() for line in f]

    result = {}
    for i in range(0, len(lines), 2):
        if i + 1 < len(lines):
            result[lines[i]] = lines[i + 1]
    return result


def parse_hea(record_id):
    hea_path = DATA_DIR / f"{record_id}.hea"
    with open(hea_path, "r") as f:
        lines = [line.strip() for line in f]

    parts = lines[0].split()
    record_name = parts[0]
    n_signals = int(parts[1])
    fs = int(parts[2])
    n_samples = int(parts[3])

    assert n_signals == EXPECTED_LEADS, f"{record_id}: expected {EXPECTED_LEADS} leads, got {n_signals}"
    assert fs == EXPECTED_FS, f"{record_id}: expected fs={EXPECTED_FS}, got {fs}"
    assert n_samples == EXPECTED_SAMPLES, f"{record_id}: expected {EXPECTED_SAMPLES} samples, got {n_samples}"

    leads = []
    gains = []
    for line in lines[1:1 + EXPECTED_LEADS]:
        fields = line.split()
        gains.append(int(fields[2]))
        leads.append(fields[8])

    assert leads == LEAD_NAMES, f"{record_id}: lead order mismatch: {leads}"

    age = None
    sex = None
    diagnoses = None
    patient_num = None
    description = None

    for line in lines[1 + EXPECTED_LEADS:]:
        line = line.lstrip("#").strip()
        age_sex_match = re.match(r"<age>:\s*(\d+)\s*<sex>:\s*(\w)\s*<diagnoses>\s*(.*)", line)
        if age_sex_match:
            age = int(age_sex_match.group(1))
            sex = age_sex_match.group(2)
            diagnoses = age_sex_match.group(3).strip()
            continue
        patient_match = re.match(r"patient\s+(\d+)", line)
        if patient_match:
            patient_num = int(patient_match.group(1))
            continue
        if line and age is not None:
            description = line

    return {
        "record_id": record_name,
        "n_leads": n_signals,
        "fs": fs,
        "n_samples": n_samples,
        "gain": gains[0],
        "leads": leads,
        "age": age,
        "sex": sex,
        "diagnoses": diagnoses,
        "patient_id": patient_num,
        "description": description,
    }


def build_metadata():
    record_ids = get_record_ids()
    patient_map = parse_patient_diagnoses()
    desc_map = parse_record_descriptions()

    rows = []
    for rid in record_ids:
        info = parse_hea(rid)
        if rid in patient_map:
            info["patient_id"] = patient_map[rid]["patient_id"]
            if not info["diagnoses"]:
                info["diagnoses"] = patient_map[rid]["diagnosis"]
        if rid in desc_map:
            info["description"] = desc_map[rid]
        rows.append(info)

    return pd.DataFrame(rows)
