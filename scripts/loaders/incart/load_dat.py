import numpy as np
from loaders.incart.config import DATA_DIR, EXPECTED_SAMPLES, EXPECTED_LEADS, MAX_SAMPLES


def load_dat(record_id, gain, adc_zero=0, max_samples=None):
    dat_path = DATA_DIR / f"{record_id}.dat"
    if max_samples is None:
        max_samples = EXPECTED_SAMPLES
    n_ints = max_samples * EXPECTED_LEADS
    raw = np.fromfile(dat_path, dtype="<i2", count=n_ints)
    n_loaded = len(raw) // EXPECTED_LEADS
    signals = raw.reshape(n_loaded, EXPECTED_LEADS).astype("f4")
    signals = (signals - adc_zero) / gain
    times = np.arange(n_loaded, dtype="f4") / 257.0
    return times, signals


def load_dat_memmap(record_id, gain, adc_zero=0, max_samples=None):
    dat_path = DATA_DIR / f"{record_id}.dat"
    if max_samples is None:
        max_samples = EXPECTED_SAMPLES
    raw = np.memmap(dat_path, dtype="<i2", mode="r",
                    shape=(max_samples, EXPECTED_LEADS))
    signals = raw.astype("f4")
    signals = (signals - adc_zero) / gain
    times = np.arange(max_samples, dtype="f4") / 257.0
    return times, signals
