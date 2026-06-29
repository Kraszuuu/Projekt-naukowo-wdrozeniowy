"""Weryfikacja integralności (SHA256) i licencji zbioru PTB-XL.

Realizuje wymóg Etapu 2: kontrola integralności wg SHA256SUMS.txt
oraz potwierdzenie licencji CC BY 4.0.
"""

import hashlib
import random

from loaders.ptbxl.config import (
    DATA_DIR, SHA256SUMS_FILE, LICENSE_FILE,
    LICENSE_EXPECTED_HEADER, KEY_FILES,
)

_CHUNK = 1 << 20  # 1 MiB


def parse_sha256sums():
    """Zwraca słownik {ścieżka_względna: oczekiwany_hash} z SHA256SUMS.txt."""
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
    """Sprawdza, czy LICENSE.txt to Creative Commons Attribution 4.0."""
    if not LICENSE_FILE.exists():
        return {"ok": False, "reason": "Brak pliku LICENSE.txt", "header": None}
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
    """Weryfikuje SHA256 plików zbioru.

    - Pliki metadanych (KEY_FILES) sprawdzane są zawsze w całości.
    - Pliki sygnałowe: losowa próbka `sample` rekordów (lub wszystkie gdy full=True).

    Zwraca raport z licznikami i listą niezgodności.
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
        # Próbkujemy po nazwie bazowej rekordu, by sprawdzać pary .dat + .hea.
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
