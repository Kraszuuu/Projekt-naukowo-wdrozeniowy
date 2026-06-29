"""Wczytywanie sygnałów EKG PTB-XL przez bibliotekę wfdb.

Realizuje kryterium zaliczenia Etapu 2: poprawne wczytanie co najmniej
100 sygnałów. Dodatkowo zbiera statystyki kształtu/zakresu sygnału.
"""

import numpy as np
import wfdb

from loaders.ptbxl.config import DATA_DIR, EXPECTED_LEADS, SAMPLING_RATE_LR


def load_signal(filename):
    """Wczytuje pojedynczy rekord WFDB. `filename` jak w kolumnie filename_lr/hr."""
    record_path = str(DATA_DIR / filename)
    signal, meta = wfdb.rdsamp(record_path)
    return signal, meta


def load_signals(df, n=100, sampling_rate=SAMPLING_RATE_LR):
    """Wczytuje pierwsze `n` rekordów i weryfikuje poprawność.

    Zwraca raport: ile wczytano, kształty, fs, zakres amplitud, błędy.
    """
    col = "filename_lr" if sampling_rate == SAMPLING_RATE_LR else "filename_hr"
    filenames = df[col].head(n).tolist()

    loaded = 0
    errors = []
    shapes = set()
    fs_values = set()
    leads_ok = True
    nan_records = 0
    amp_min, amp_max = np.inf, -np.inf

    for fn in filenames:
        try:
            signal, meta = load_signal(fn)
        except Exception as exc:  # noqa: BLE001 - chcemy zebrać wszystkie błędy
            errors.append({"filename": fn, "error": str(exc)})
            continue
        loaded += 1
        shapes.add(signal.shape)
        fs_values.add(int(meta.get("fs", -1)))
        if signal.shape[1] != EXPECTED_LEADS:
            leads_ok = False
        if np.isnan(signal).any():
            nan_records += 1
        amp_min = min(amp_min, float(np.nanmin(signal)))
        amp_max = max(amp_max, float(np.nanmax(signal)))

    return {
        "requested": len(filenames),
        "loaded": loaded,
        "sampling_rate_requested": sampling_rate,
        "fs_observed": sorted(fs_values),
        "shapes": sorted(str(s) for s in shapes),
        "all_12_leads": leads_ok,
        "records_with_nan": nan_records,
        "amplitude_range_mV": [
            round(amp_min, 3) if np.isfinite(amp_min) else None,
            round(amp_max, 3) if np.isfinite(amp_max) else None,
        ],
        "errors": errors,
        "passed": loaded >= 100,
    }
