"""Etap 2 — Wybór i Weryfikacja Danych (PTB-XL).

Orkiestruje pełną weryfikację:
  1. Licencja (CC BY 4.0)
  2. Integralność SHA256
  3. Eksploracja metadanych + mapowanie 5 nadklas
  4. Wczytanie >= 100 sygnałów przez wfdb
  5. Zapis raportu weryfikacyjnego

Uruchomienie (z katalogu głównego projektu, aktywne środowisko):
    python -m loaders.ptbxl.main                 # próbka 100 rekordów do SHA256
    python -m loaders.ptbxl.main --sha-sample 500
    python -m loaders.ptbxl.main --full-sha      # pełna weryfikacja SHA256 (wolne)
    python -m loaders.ptbxl.main --signals 200

Wymaga, by katalog `scripts/` był na sys.path (patrz blok __main__).
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

# Umożliwia uruchomienie skryptu bezpośrednio (python scripts/loaders/ptbxl/main.py)
# oraz jako moduł (python -m loaders.ptbxl.main) — katalog scripts/ trafia na sys.path.
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from loaders.ptbxl.config import SUPERCLASSES
from loaders.ptbxl.verify_integrity import verify_license, verify_files
from loaders.ptbxl import metadata as md
from loaders.ptbxl.signals import load_signals
from loaders.ptbxl.report import save_report


def run(sha_sample=100, full_sha=False, n_signals=100, min_likelihood=0.0):
    print("=" * 70)
    print("ETAP 2 — Weryfikacja danych PTB-XL")
    print("=" * 70)

    print("\n[1/5] Weryfikacja licencji...")
    license_report = verify_license()
    print(f"      Licencja: {'OK' if license_report['ok'] else 'NIEZGODNA'} "
          f"— {license_report['header']}")

    print("\n[2/5] Weryfikacja integralności SHA256 "
          f"({'pełna' if full_sha else f'próbka {sha_sample} rekordów'})...")
    integrity_report = verify_files(sample=sha_sample, full=full_sha)
    print(f"      Sprawdzono {integrity_report['checked']:,} plików — "
          f"zgodne: {integrity_report['ok']:,}, "
          f"niezgodne: {len(integrity_report['mismatch'])}, "
          f"brakujące: {len(integrity_report['missing'])}")

    print("\n[3/5] Wczytywanie i eksploracja metadanych...")
    df = md.load_metadata()
    agg_df = md.load_scp_statements()
    df = md.add_superclasses(df, agg_df, min_likelihood=min_likelihood)

    metadata_report = {
        "n_records": int(len(df)),
        "demographics": md.demographics(df),
        "fold_distribution": md.fold_distribution(df),
        "superclass_distribution": md.superclass_distribution(df),
        "label_cooccurrence": md.label_cooccurrence(df),
        "missing_data": md.missing_data(df),
        "min_likelihood_threshold": min_likelihood,
    }
    dist = metadata_report["superclass_distribution"]
    print(f"      Rekordów: {metadata_report['n_records']:,} | "
          f"pacjentów: {metadata_report['demographics']['n_patients']:,}")
    print("      Rozkład 5 nadklas:")
    for cls in SUPERCLASSES:
        print(f"        {cls:5s}: {dist[cls]['count']:6,d}  ({dist[cls]['pct']:.2f}%)")

    print("\n[4/5] Wczytywanie sygnałów przez wfdb...")
    signals_report = load_signals(df, n=n_signals)
    print(f"      Wczytano {signals_report['loaded']}/{signals_report['requested']} "
          f"sygnałów — {'PASS' if signals_report['passed'] else 'FAIL'}")

    passed = (
        license_report["ok"]
        and integrity_report["passed"]
        and signals_report["passed"]
    )

    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "dataset": "PTB-XL v1.0.3",
        "license": license_report,
        "integrity": integrity_report,
        "metadata": metadata_report,
        "signals": signals_report,
        "passed": passed,
    }

    print("\n[5/5] Zapis raportu...")
    paths = save_report(report)
    for kind, path in paths.items():
        if path is not None:
            print(f"      {kind}: {path}")

    print("\n" + "=" * 70)
    print(f"WYNIK ETAPU 2: {'ZALICZONY' if passed else 'NIEZALICZONY'}")
    print("=" * 70)
    return report


def parse_args():
    p = argparse.ArgumentParser(description="Etap 2 — weryfikacja danych PTB-XL")
    p.add_argument("--sha-sample", type=int, default=100,
                   help="Liczba rekordów sygnałowych do weryfikacji SHA256 (domyślnie 100)")
    p.add_argument("--full-sha", action="store_true",
                   help="Pełna weryfikacja SHA256 wszystkich plików (wolne)")
    p.add_argument("--signals", type=int, default=100,
                   help="Liczba sygnałów do wczytania przez wfdb (domyślnie 100)")
    p.add_argument("--min-likelihood", type=float, default=0.0,
                   help="Minimalna pewność SCP do zaliczenia nadklasy (0=każde wystąpienie)")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run(
        sha_sample=args.sha_sample,
        full_sha=args.full_sha,
        n_signals=args.signals,
        min_likelihood=args.min_likelihood,
    )
