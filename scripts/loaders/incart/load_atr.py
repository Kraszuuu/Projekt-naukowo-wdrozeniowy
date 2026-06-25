import wfdb
import numpy as np
import pandas as pd
from loaders.incart.config import DATA_DIR


ANNOTATION_SYMBOLS = {
    "N": "normal beat",
    "L": "left bundle branch block beat",
    "R": "right bundle branch block beat",
    "B": "bundle branch block beat",
    "A": "atrial premature beat",
    "a": "aberrant atrial premature beat",
    "J": "nodal (junctional) premature beat",
    "S": "supraventricular premature or ectopic beat",
    "V": "premature ventricular contraction",
    "r": "R-on-T premature ventricular contraction",
    "F": "fusion of ventricular and normal beat",
    "e": "atrial escape beat",
    "j": "nodal (junctional) escape beat",
    "E": "ventricular escape beat",
    "/": "paced beat",
    "f": "fusion of paced and normal beat",
    "Q": "unclassifiable beat",
    "?": "beat not classified during learning",
    "|": "isolated QRS-like artifact",
    "[": "start of ventricular flutter/fibrillation",
    "!": "ventricular flutter wave",
    "]": "end of ventricular flutter/fibrillation",
    "x": "non-conducted P-wave (blocked APC)",
    "(": "waveform onset",
    ")": "waveform end",
    "p": "peak of P-wave",
    "t": "peak of T-wave",
    "u": "peak of U-wave",
    "`": "PQ junction",
    "'": "J-point",
    "^": "(non-captured) pacemaker artifact",
    "=": "measurement annotation",
    '"': "comment annotation",
    "@": "link to external data",
    "+": "change in signal quality",
    "~": "change in signal quality",
}


def load_atr(record_id, fs=257):
    record_path = DATA_DIR / record_id
    ann = wfdb.rdann(str(record_path), "atr")

    samples = ann.sample
    symbols = ann.symbol

    df = pd.DataFrame({
        "record_id": record_id,
        "sample_index": samples,
        "time": np.array(samples, dtype="f4") / fs,
        "symbol": symbols,
        "description": [ANNOTATION_SYMBOLS.get(s, "unknown") for s in symbols],
    })

    return df
