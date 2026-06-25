import pandas as pd
import numpy as np
from loaders.incart.config import LEAD_NAMES


def build_record_wide_df(record_id, times, signals_mv, meta):
    n_samples = signals_mv.shape[0]
    df = pd.DataFrame({
        "record_id": record_id,
        "sample_index": np.arange(n_samples, dtype="i8"),
        "time": times,
    })
    for i, lead in enumerate(LEAD_NAMES):
        df[lead] = signals_mv[:, i]

    meta_cols = {
        "patient_id": meta["patient_id"],
        "age": meta["age"],
        "sex": meta["sex"],
        "diagnoses": meta["diagnoses"],
        "description": meta["description"],
        "fs": meta["fs"],
        "gain": meta["gain"],
    }
    for col, val in meta_cols.items():
        df[col] = val

    return df


def make_long(wide_df):
    if "voltage_mV" in wide_df.columns:
        return wide_df
    id_cols = [c for c in [
        "record_id", "sample_index", "time", "patient_id", "age",
        "sex", "diagnoses", "description", "fs", "gain",
    ] if c in wide_df.columns]
    return wide_df.melt(
        id_vars=id_cols,
        value_vars=LEAD_NAMES,
        var_name="lead",
        value_name="voltage_mV",
    ).sort_values(["sample_index", "lead"]).reset_index(drop=True)


def build_record_long_df(record_id, times, signals_mv, meta):
    wide = build_record_wide_df(record_id, times, signals_mv, meta)
    return make_long(wide)
