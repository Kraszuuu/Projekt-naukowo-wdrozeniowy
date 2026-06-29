"""Assembling and saving the Stage 2 verification report for PTB-XL."""

import json
from datetime import datetime

import pandas as pd

from loaders.ptbxl.config import OUTPUT_DIR, SUPERCLASSES


def save_report(report):
    """Saves the report as JSON, readable TXT, class-distribution CSV and a plot."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    json_path = OUTPUT_DIR / "verification_report.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    txt_path = OUTPUT_DIR / "verification_report.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(_render_text(report))

    csv_path = _save_class_distribution_csv(report)
    plot_path = _save_class_distribution_plot(report)

    return {
        "json": json_path,
        "txt": txt_path,
        "class_distribution_csv": csv_path,
        "class_distribution_plot": plot_path,
    }


def _save_class_distribution_csv(report):
    dist = report["metadata"]["superclass_distribution"]
    rows = [
        {"superclass": cls, "count": dist[cls]["count"], "pct": dist[cls]["pct"]}
        for cls in SUPERCLASSES
    ]
    rows.append({
        "superclass": "UNLABELED",
        "count": dist["__unlabeled__"]["count"],
        "pct": dist["__unlabeled__"]["pct"],
    })
    path = OUTPUT_DIR / "class_distribution.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def _save_class_distribution_plot(report):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return None

    dist = report["metadata"]["superclass_distribution"]
    counts = [dist[c]["count"] for c in SUPERCLASSES]

    fig, ax = plt.subplots(figsize=(7, 4.5))
    bars = ax.bar(SUPERCLASSES, counts, color="#3b6ea5")
    ax.set_title("PTB-XL — rozkład 5 nadklas diagnostycznych")
    ax.set_ylabel("Liczba rekordów")
    ax.bar_label(bars)
    fig.tight_layout()

    path = OUTPUT_DIR / "class_distribution.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def _render_text(report):
    lines = []
    w = lines.append

    w("=" * 70)
    w("RAPORT WERYFIKACYJNY — ETAP 2 — PTB-XL")
    w(f"Wygenerowano: {report['generated_at']}")
    w("=" * 70)

    lic = report["license"]
    w("\n[1] LICENCJA")
    w(f"  Status : {'OK (CC BY 4.0)' if lic['ok'] else 'NIEZGODNA'}")
    w(f"  Nagłówek: {lic['header']}")

    integ = report["integrity"]
    w("\n[2] INTEGRALNOŚĆ (SHA256)")
    w(f"  Wpisów w SHA256SUMS.txt : {integ['total_in_sha256sums']:,}")
    w(f"  Sprawdzono plików       : {integ['checked']:,}")
    w(f"  Rekordów sygnałowych    : {integ['signal_records_checked']:,} "
      f"({'pełna' if integ['full'] else 'próbka'})")
    w(f"  Zgodne                  : {integ['ok']:,}")
    w(f"  Niezgodne               : {len(integ['mismatch'])}")
    w(f"  Brakujące               : {len(integ['missing'])}")
    w(f"  Wynik                   : {'PASS' if integ['passed'] else 'FAIL'}")

    meta = report["metadata"]
    w("\n[3] METADANE")
    w(f"  Liczba rekordów EKG : {meta['n_records']:,}")
    w(f"  Liczba pacjentów    : {meta['demographics']['n_patients']:,}")
    age = meta["demographics"]["age"]
    w(f"  Wiek                : min={age['min']}, max={age['max']}, "
      f"śr={age['mean']}, mediana={age['median']}")
    w(f"  Płeć                : {meta['demographics']['sex']}")

    fold = meta["fold_distribution"]
    w("\n[4] PODZIAŁ FOLDÓW")
    w(f"  Trening (foldy 1-8) : {fold['train_folds_1_8']:,}")
    w(f"  Walidacja (fold 9)  : {fold['val_fold_9']:,}")
    w(f"  Test (fold 10)      : {fold['test_fold_10']:,}")

    dist = meta["superclass_distribution"]
    w("\n[5] ROZKŁAD 5 NADKLAS DIAGNOSTYCZNYCH")
    for cls in SUPERCLASSES:
        w(f"  {cls:5s}: {dist[cls]['count']:6,d}  ({dist[cls]['pct']:5.2f}%)")
    w(f"  {'BRAK':5s}: {dist['__unlabeled__']['count']:6,d}  "
      f"({dist['__unlabeled__']['pct']:5.2f}%)")

    missing = meta["missing_data"]
    w("\n[6] BRAKI DANYCH (kolumny z brakami)")
    if not missing:
        w("  Brak braków.")
    else:
        for col, info in list(missing.items())[:15]:
            w(f"  {col:28s}: {info['missing']:6,d}  ({info['pct']:5.2f}%)")

    sig = report["signals"]
    w("\n[7] WCZYTANIE SYGNAŁÓW (wfdb)")
    w(f"  Żądano              : {sig['requested']}")
    w(f"  Wczytano poprawnie  : {sig['loaded']}")
    w(f"  fs zaobserwowane    : {sig['fs_observed']} Hz")
    w(f"  Kształty            : {sig['shapes']}")
    w(f"  Wszystkie 12 odpr.  : {sig['all_12_leads']}")
    w(f"  Zakres amplitud     : {sig['amplitude_range_mV']} mV")
    w(f"  Wynik (>=100)       : {'PASS' if sig['passed'] else 'FAIL'}")

    w("\n" + "=" * 70)
    w(f"WYNIK KOŃCOWY ETAPU 2: {'ZALICZONY' if report['passed'] else 'NIEZALICZONY'}")
    w("=" * 70)

    return "\n".join(lines) + "\n"
