"""Integrity (SHA256) and license verification for the PTB-XL dataset.

Implements the Stage 2 requirement: integrity check against SHA256SUMS.txt
and confirmation of the CC BY 4.0 license.
"""

import hashlib
import random

from loaders.ptbxl.config import (
    DATA_DIR, SHA256SUMS_FILE, LICENSE_FILE,
    LICENSE_EXPECTED_HEADER, KEY_FILES,
)

_CHUNK = 1 << 20  # 1 MiB


def parse_sha256sums():
    """Returns a dict {relative_path: expected_hash} from SHA256SUMS.txt."""
    sums = {}
    with open(SHA256SUMS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            digest, _, name = line.partition(" ")
            name = name.strip().lstrip("*")
            if name:
                sums[name] = digest
    return sums


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(_CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_license():
    """Checks whether LICENSE.txt is Creative Commons Attribution 4.0."""
    if not LICENSE_FILE.exists():
        return {"ok": False, "reason": "Missing LICENSE.txt file", "header": None}
    with open(LICENSE_FILE, "r", encoding="utf-8") as f:
        header = f.readline().strip()
    ok = LICENSE_EXPECTED_HEADER.lower() in header.lower()
    return {"ok": ok, "header": header, "expected": LICENSE_EXPECTED_HEADER}


def _verify_one(rel_name, sums):
    path = DATA_DIR / rel_name
    if not path.exists():
        return "missing"
    expected = sums.get(rel_name.replace("\\", "/"))
    if expected is None:
        return "no_reference"
    return "ok" if sha256_of(path) == expected else "mismatch"


def verify_files(sample=100, full=False, seed=0):
    """Verifies SHA256 of the dataset files.

    - Metadata files (KEY_FILES) are always checked in full.
    - Signal files: a random sample of `sample` records (or all when full=True).

    Returns a report with counters and a list of mismatches.
    """
    sums = parse_sha256sums()

    signal_files = sorted(
        n for n in sums
        if (n.endswith(".dat") or n.endswith(".hea"))
        and (n.startswith("records100/") or n.startswith("records500/"))
    )

    if full:
        to_check_signals = signal_files
    else:
        rng = random.Random(seed)
        # Sample by record base name to check .dat + .hea pairs together.
        bases = sorted({n.rsplit(".", 1)[0] for n in signal_files})
        chosen = set(rng.sample(bases, min(sample, len(bases))))
        to_check_signals = [n for n in signal_files if n.rsplit(".", 1)[0] in chosen]

    targets = list(KEY_FILES) + to_check_signals

    results = {"ok": [], "mismatch": [], "missing": [], "no_reference": []}
    for rel in targets:
        status = _verify_one(rel, sums)
        results[status].append(rel)

    return {
        "total_in_sha256sums": len(sums),
        "checked": len(targets),
        "signal_records_checked": len({n.rsplit('.', 1)[0] for n in to_check_signals}),
        "full": full,
        "ok": len(results["ok"]),
        "mismatch": results["mismatch"],
        "missing": results["missing"],
        "no_reference": results["no_reference"],
        "passed": not results["mismatch"] and not results["missing"],
    }
