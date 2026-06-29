"""Loading and exploration of PTB-XL metadata (ptbxl_database.csv).

Maps SCP-ECG codes to the 5 diagnostic superclasses (NORM, MI, STTC, CD, HYP)
and computes class, fold, demographic and missing-data distributions.
"""

import ast

import numpy as np
import pandas as pd

from loaders.ptbxl.config import (
    DATABASE_CSV, SCP_STATEMENTS_CSV, SUPERCLASSES,
    TRAIN_FOLDS, VAL_FOLD, TEST_FOLD,
)


def load_metadata():
    """Loads ptbxl_database.csv and parses the scp_codes column into dicts."""
    df = pd.read_csv(DATABASE_CSV, index_col="ecg_id")
    df["scp_codes"] = df["scp_codes"].apply(ast.literal_eval)
    return df


def load_scp_statements():
    """Loads scp_statements.csv and returns only the diagnostic statements."""
    agg = pd.read_csv(SCP_STATEMENTS_CSV, index_col=0)
    return agg[agg["diagnostic"] == 1]


def _make_aggregator(agg_df, min_likelihood=0.0):
    classes = agg_df["diagnostic_class"].to_dict()

    def aggregate(scp_dict):
        out = set()
        for code, likelihood in scp_dict.items():
            if code in classes and likelihood >= min_likelihood:
                out.add(classes[code])
        return sorted(out)

    return aggregate


def add_superclasses(df, agg_df, min_likelihood=0.0):
    """Adds a diagnostic_superclass column (list of superclasses) to the frame."""
    aggregate = _make_aggregator(agg_df, min_likelihood=min_likelihood)
    df = df.copy()
    df["diagnostic_superclass"] = df["scp_codes"].apply(aggregate)
    return df


def superclass_distribution(df):
    """Distribution of the 5 superclasses (multi-label: a record may have >1)."""
    counts = {cls: 0 for cls in SUPERCLASSES}
    n_unlabeled = 0
    for labels in df["diagnostic_superclass"]:
        if not labels:
            n_unlabeled += 1
        for lab in labels:
            if lab in counts:
                counts[lab] += 1
    total = len(df)
    dist = {
        cls: {"count": c, "pct": round(100 * c / total, 2)}
        for cls, c in counts.items()
    }
    dist["__unlabeled__"] = {
        "count": n_unlabeled,
        "pct": round(100 * n_unlabeled / total, 2),
    }
    return dist


def fold_distribution(df):
    """Record distribution by strat_fold and the suggested train/val/test split."""
    per_fold = df["strat_fold"].value_counts().sort_index().to_dict()
    per_fold = {int(k): int(v) for k, v in per_fold.items()}
    train = int(df["strat_fold"].isin(TRAIN_FOLDS).sum())
    val = int((df["strat_fold"] == VAL_FOLD).sum())
    test = int((df["strat_fold"] == TEST_FOLD).sum())
    return {
        "per_fold": per_fold,
        "train_folds_1_8": train,
        "val_fold_9": val,
        "test_fold_10": test,
    }


def demographics(df):
    age = df["age"]
    sex = df["sex"].map({0: "male", 1: "female"}).value_counts().to_dict()
    return {
        "n_patients": int(df["patient_id"].nunique()),
        "age": {
            "min": float(np.nanmin(age)),
            "max": float(np.nanmax(age)),
            "mean": round(float(np.nanmean(age)), 2),
            "median": float(np.nanmedian(age)),
        },
        "sex": {str(k): int(v) for k, v in sex.items()},
    }


def missing_data(df):
    """Count and percentage of missing values in metadata columns."""
    na = df.isna().sum()
    na = na[na > 0].sort_values(ascending=False)
    total = len(df)
    return {
        col: {"missing": int(n), "pct": round(100 * int(n) / total, 2)}
        for col, n in na.items()
    }


def label_cooccurrence(df):
    """Superclass co-occurrence matrix (how many records share a class pair)."""
    mat = {a: {b: 0 for b in SUPERCLASSES} for a in SUPERCLASSES}
    for labels in df["diagnostic_superclass"]:
        for a in labels:
            for b in labels:
                if a in mat and b in mat[a]:
                    mat[a][b] += 1
    return mat
