# ECG Trustworthiness Benchmark

Wieloaspektowa ocena wiarygodności modeli głębokiego uczenia do klasyfikacji arytmii EKG – wyjaśnialność, kalibracja niepewności, odporność na domain shift.

---

## Setup

### Wymagania

- Python 3.11 (działa też 3.10 / 3.12)
- Zalecany GPU NVIDIA z CUDA 12.1 (sterownik ≥ 525). Bez GPU – patrz uwaga niżej.

### Automatycznie (Windows)

```powershell
.\scripts\setup_env.ps1
.\.venv\Scripts\Activate.ps1
```

Skrypt tworzy środowisko `.venv`, instaluje zależności z `requirements.txt` i zapisuje zamrożone wersje do `requirements-locked.txt`.

### Ręcznie

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pip freeze > requirements-locked.txt   # zamrożenie wersji
```

Na Linux/macOS aktywacja środowiska: `source .venv/bin/activate`.

> **Bez GPU NVIDIA?** W `requirements.txt` usuń linię `--extra-index-url ...` oraz sufiksy `+cu121`, aby zainstalować wersję CPU PyTorcha.

Po zamrożeniu commitnij `requirements-locked.txt`, aby każdy członek zespołu miał identyczne wersje.

---

## Struktura

| Katalog | Zawartość |
|---|---|
| `data/raw/{incart,ptb-xl,chapman-shaoxing}/` | Dane źródłowe (read‑only) |
| `data/processed/{dataset}/` | Artefakty przetwarzania (sygnały, splity) |
| `data/features/{dataset}/` | Cechy dla modeli baseline |
| `scripts/loaders/incart/` | Loader INCART |
| `scripts/train/` | Trening modeli |
| `scripts/utils/` | Helpery (metrki, wizualizacje) |
| `models/ptb-xl/` | Wagi trenowane na PTB-XL |
| `notebooks/` | Jupyter Notebooki |
| `results/{ptb-xl,domain_shift,robustness}/` | Wyniki per scenariusz |
| `experiments/` | Konfiguracje i logi |
| `docs/` | Przegląd literatury, raporty |

---

## Importy

```python
import sys
sys.path.insert(0, "ścieżka/do/projektu/scripts")
from loaders.incart.config import DATA_DIR
```

---

## Konwencje

- **Kod** → `scripts/{loaders,train,utils}/`
- **Dane źródłowe** → `data/raw/{dataset}/` (nigdy nie modyfikować ręcznie)
- **Artefakty** → `data/processed/{dataset}/`
- **Wyniki** → `results/{scenariusz}/{dataset}/`
- **Wagi** → `models/{dataset_treningowy}/{architektura}/`

---

## Docker (TODO)

Dla w pełni powtarzalnego środowiska – niezależnego od OS i sterowników CUDA – planowane jest dodanie `Dockerfile` bazującego na `pytorch/pytorch:2.5.1-cuda12.1-cudnn9-runtime`.

```bash
# docelowo:
docker build -t ecg-trust .
docker run --gpus all -v $(pwd):/workspace -it ecg-trust
```
