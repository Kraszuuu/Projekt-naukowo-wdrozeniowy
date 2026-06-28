#!/usr/bin/env python3
"""Download ECG datasets from PhysioNet if not already present."""

import shutil
import zipfile
import tarfile
import urllib.request
import os
import sys
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"

DATASETS = [
    {
        "name": "ptb-xl",
        "url": "https://physionet.org/files/ptb-xl/1.0.3/",
        "dir": DATA_RAW / "ptb-xl",
    },
    {
        "name": "chapman-shaoxing",
        "url": "https://physionet.org/files/ecg-arrhythmia/1.0.0/",
        "dir": DATA_RAW / "chapman-shaoxing",
    },
    {
        "name": "incart",
        "url": "https://physionet.org/files/incartdb/1.0.0/",
        "dir": DATA_RAW / "incart" / "files",
    },
]


class PhysioNetParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self._links = []
        self._in_pre = False
        self._in_a = False
        self._href = ""
        self._pre_depth = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "pre":
            self._in_pre = True
        if self._in_pre and tag == "a":
            self._in_a = True
            self._href = attrs.get("href", "")

    def handle_endtag(self, tag):
        if tag == "pre":
            self._in_pre = False
        if self._in_a and tag == "a":
            self._in_a = False

    def handle_data(self, data):
        if self._in_a and self._href:
            name = data.strip()
            if name and name not in ("Parent Directory", "../", "../"):
                is_dir = self._href.endswith("/")
                self._links.append((name, self._href, is_dir))

    @property
    def links(self):
        return self._links


def list_remote(url: str) -> list[tuple[str, str, bool]]:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; ECGTrust/1.0)"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    parser = PhysioNetParser()
    parser.feed(html)
    return parser.links


def download_file(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)

    if dest.exists():
        local_size = dest.stat().st_size
        req = urllib.request.Request(url, method="HEAD")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                remote_size = int(resp.headers.get("Content-Length", 0))
            if remote_size > 0 and local_size >= remote_size:
                return
        except Exception:
            pass

    tmp = dest.with_suffix(dest.suffix + ".part")
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; ECGTrust/1.0)"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        total = int(resp.headers.get("Content-Length", 0))
        dl = 0
        with open(tmp, "wb") as f:
            while True:
                chunk = resp.read(8192)
                if not chunk:
                    break
                f.write(chunk)
                dl += len(chunk)
    tmp.rename(dest)


def _walk(url: str, dest: Path) -> None:
    items = list_remote(url)
    for name, href, is_dir in items:
        full_url = urljoin(url, href)
        if is_dir:
            sub = dest / name
            sub.mkdir(parents=True, exist_ok=True)
            _walk(full_url, sub)
        else:
            out = dest / name
            print(f"  {out.name}")
            download_file(full_url, out)


def download(ds: dict) -> None:
    name = ds["name"]
    url = ds["url"]
    dest = ds["dir"]

    print(f"\n{'='*60}")
    print(f"Downloading {name} ...")
    print(f"  from: {url}")
    print(f"  to:   {dest}")
    print(f"{'='*60}")

    dest.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    try:
        _walk(url, dest)
    except Exception as e:
        print(f"  Error: {e}")
        print("  Retry with: wget -r -N -c -np -nH --cut-dirs=3 -P <dir> <url>")
        return

    elapsed = time.time() - t0
    print(f"  Downloaded in {elapsed:.0f}s")

    extract_archives(dest)

    print(f"  Done — {name}\n")


def extract_archives(directory: Path) -> None:
    for item in sorted(directory.iterdir()):
        name = item.name.lower()
        if name.endswith(".zip"):
            print(f"  Extracting {item.name} ...")
            with zipfile.ZipFile(item) as zf:
                zf.extractall(directory)
            item.unlink()
        elif name.endswith(".tar.gz") or name.endswith(".tgz"):
            print(f"  Extracting {item.name} ...")
            with tarfile.open(item) as tf:
                tf.extractall(directory)
            item.unlink()
        elif name.endswith(".tar.bz2"):
            print(f"  Extracting {item.name} ...")
            with tarfile.open(item) as tf:
                tf.extractall(directory)
            item.unlink()

    subdirs = [p for p in directory.iterdir() if p.is_dir()]
    if len(subdirs) == 1:
        single = subdirs[0]
        has_data = any(
            f.suffix in {".dat", ".hea", ".atr", ".csv", ".mat", ".txt", ".sqlite"}
            or f.is_dir()
            for f in single.rglob("*")
            if not f.name.startswith(".")
        )
        if has_data:
            print(f"  Flattening {single.name}/")
            for item in list(single.iterdir()):
                target = directory / item.name
                if target.exists():
                    if target.is_dir():
                        shutil.copytree(item, target, dirs_exist_ok=True)
                        shutil.rmtree(item)
                    else:
                        target.unlink()
                        item.rename(target)
                else:
                    item.rename(target)
            shutil.rmtree(single)


def has_data(directory: Path) -> bool:
    if not directory.exists():
        return False
    for item in directory.iterdir():
        name = item.name
        if name == ".gitkeep" or name == "README":
            continue
        if item.is_file() or item.is_dir():
            return True
    return False


def main() -> None:
    missing = [ds for ds in DATASETS if not has_data(ds["dir"])]

    if not missing:
        print("All datasets already present. Nothing to do.")
        return

    print(f"Datasets to download: {[ds['name'] for ds in missing]}\n")

    for ds in DATASETS:
        if has_data(ds["dir"]):
            print(f"{ds['name']}: already present, skipping.")
        else:
            download(ds)

    print("\n" + "=" * 60)
    print("Download summary:")
    all_ok = True
    for ds in DATASETS:
        ok = has_data(ds["dir"])
        status = "OK" if ok else "MISSING"
        if not ok:
            all_ok = False
        print(f"  {ds['name']}: {status}")
    print("=" * 60)
    if not all_ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
