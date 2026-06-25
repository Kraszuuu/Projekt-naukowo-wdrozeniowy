import time
import shutil
from pathlib import Path
import pandas as pd
from loaders.incart.config import (
    SIGNAL_PARTITION_DIR, ANNOTATION_PARTITION_DIR, DATA_DIR, MAX_SAMPLES,
)
from loaders.incart.parse_hea import get_record_ids, parse_hea, parse_patient_diagnoses, parse_record_descriptions
from loaders.incart.load_dat import load_dat
from loaders.incart.load_atr import load_atr
from loaders.incart.build_dataframe import build_record_wide_df


DTYPE_MAP = {
    "record_id": "str",
    "sex": "category",
    "diagnoses": "category",
    "description": "category",
}


def log(msg):
    print(f"  {msg}")


def run():
    record_ids = get_record_ids()
    patient_map = parse_patient_diagnoses()
    desc_map = parse_record_descriptions()

    n_records = len(record_ids)
    print(f"Building partitioned dataset from {n_records} ECG records...")

    if SIGNAL_PARTITION_DIR.exists():
        shutil.rmtree(SIGNAL_PARTITION_DIR)
    if ANNOTATION_PARTITION_DIR.exists():
        shutil.rmtree(ANNOTATION_PARTITION_DIR)

    t_start = time.time()

    for idx, rid in enumerate(record_ids):
        t_rec = time.time()
        print(f"[{idx + 1:2d}/{n_records}] {rid}:")

        # --- Load header ---
        meta = parse_hea(rid)
        if rid in patient_map:
            meta["patient_id"] = patient_map[rid]["patient_id"]
            if not meta["diagnoses"]:
                meta["diagnoses"] = patient_map[rid]["diagnosis"]
        if rid in desc_map:
            meta["description"] = desc_map[rid]
        log(f"Loaded header: {meta['n_leads']} leads, {meta['fs']} Hz, loading {MAX_SAMPLES or meta['n_samples']:,} / {meta['n_samples']:,} samples")

        # --- Load binary signal ---
        t0 = time.time()
        times, signals_mv = load_dat(rid, meta["gain"], max_samples=MAX_SAMPLES)
        dat_size = (DATA_DIR / f"{rid}.dat").stat().st_size
        log(f"Read binary signal: {dat_size / 1e6:.1f} MB, {signals_mv.shape[0]:,} × {signals_mv.shape[1]}  ({time.time() - t0:.1f}s)")

        # --- Build DataFrame (wide) ---
        t0 = time.time()
        df_sig = build_record_wide_df(rid, times, signals_mv, meta)
        for col, dtype in DTYPE_MAP.items():
            if col in df_sig.columns:
                df_sig[col] = df_sig[col].astype(dtype)
        log(f"Built wide DataFrame: {df_sig.shape[0]:,} rows × {df_sig.shape[1]} cols  ({time.time() - t0:.1f}s)")

        # --- Write signal parquet ---
        t0 = time.time()
        sig_out = SIGNAL_PARTITION_DIR / f"record_id={rid}"
        sig_out.mkdir(parents=True, exist_ok=True)
        df_sig_to_write = df_sig.drop(columns=["record_id"])
        df_sig_to_write.to_parquet(
            sig_out / "part-00000.parquet",
            compression="zstd",
            row_group_size=100000,
            version="2.6",
        )
        sig_mb = _dir_size(sig_out)
        log(f"Wrote signal parquet: {sig_mb:.1f} MB  ({time.time() - t0:.1f}s)")

        # --- Load annotations ---
        t0 = time.time()
        df_atr = load_atr(rid, meta["fs"])
        for col, dtype in DTYPE_MAP.items():
            if col in df_atr.columns:
                df_atr[col] = df_atr[col].astype(dtype)
        log(f"Loaded annotations: {df_atr.shape[0]:,} rows  ({time.time() - t0:.1f}s)")

        # --- Write annotation parquet ---
        t0 = time.time()
        atr_out = ANNOTATION_PARTITION_DIR / f"record_id={rid}"
        atr_out.mkdir(parents=True, exist_ok=True)
        df_atr_to_write = df_atr.drop(columns=["record_id"])
        df_atr_to_write.to_parquet(
            atr_out / "part-00000.parquet",
            compression="zstd",
            version="2.6",
        )
        atr_mb = _dir_size(atr_out)
        log(f"Wrote annotation parquet: {atr_mb:.2f} MB  ({time.time() - t0:.1f}s)")

        elapsed = time.time() - t_rec
        log(f"Done — {elapsed:.1f}s total")

    total = time.time() - t_start
    print(f"\nFinished in {total:.1f}s total")

    sig_size = _dir_size(SIGNAL_PARTITION_DIR)
    atr_size = _dir_size(ANNOTATION_PARTITION_DIR)
    print(f"Signal partitions: {sig_size:.1f} MB")
    print(f"Annotation partitions: {atr_size:.1f} MB")


def _dir_size(path: Path) -> float:
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file()) / (1024 * 1024)


if __name__ == "__main__":
    run()
