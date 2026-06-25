# Plan Działania – Ocena wiarygodności modeli głębokiego uczenia do klasyfikacji arytmii EKG

## Stan obecny projektu (czerwiec 2026)

- **INCART** – pobrany i przetworzony do `data/ecg_signals/` i `data/ecg_annotations/` (75 partycji, 417 próbek/record)
- **PTB-XL i Chapman-Shaoxing** – brak (do pobrania z PhysioNet)
- Brak `requirements.txt`, `README.md`, repozytorium Git
- Brak modeli, skryptów treningowych, środowiska GPU
- Istnieje `OldProject/` – warto sprawdzić, czy zawiera przydatne artefakty

---

## Etap 1 – Przegląd literatury

**Cel:** Zrozumienie state-of-the-art w zaufanej AI i klasyfikacji EKG

| Lp | Zadanie | Opis | Plik wynikowy |
|---|---|---|---|
| 1.1 | Selekcja literatury | Wyselekcjonować min. 15 prac z listy w Sekcji 12 dokumentu Projekt_zastępczy.pdf | `docs/literature_selection.md` |
| 1.2 | Lektura i notatki | Dla każdej pracy: cel, metody, zbiory danych, kluczowe wyniki, ograniczenia | `docs/literature_notes.md` |
| 1.3 | Tabela porównawcza XAI | Zestawienie metod XAI (SHAP, LIME, Grad-CAM, Integrated Gradients) stosowanych do EKG – zalety, wady, biblioteki | `docs/xai_comparison_table.md` |
| 1.4 | Dokument przeglądowy (3-5 str.) | Synteza: luka badawcza, stan wiedzy dla każdego z 3 aspektów (wyjaśnialność, kalibracja, domain shift) | `docs/literature_review.md` |

**Obowiązkowe prace do pokrycia:**
- [6] Wagner et al. (PTB-XL)
- [15] Guo et al. (Temperature Scaling)
- [16] Ballas & Diou (Domain Generalization ECG/EEG)
- [1] Zhao et al. (cross-dataset domain generalization)
- [2] Bellotti & Zhao (Conformal Prediction)

**Kryterium zaliczenia:** Akceptacja prowadzącego; pokrycie ≥5 prac obowiązkowych

---

## Etap 2 – Wybór i Weryfikacja Danych

**Cel:** Potwierdzenie dostępności, licencji i struktury danych

| Lp | Zadanie | Opis | Plik wynikowy |
|---|---|---|---|
| 2.1 | Pobranie PTB-XL | `wget -r -N -c -np https://physionet.org/files/ptb-xl/1.0.3/` → `data/ptb-xl/` | `data/ptb-xl/` |
| 2.2 | Pobranie Chapman-Shaoxing | `wget -r -N -c -np https://physionet.org/files/ecg-arrhythmia/1.0.0/` → `data/chapman-shaoxing/` | `data/chapman-shaoxing/` |
| 2.3 | Weryfikacja integralności | Sprawdzenie SHA256 względem `SHA256SUMS.txt` dla obu zbiorów | `docs/verification_report.md` |
| 2.4 | Eksploracja PTB-XL | Wczytanie `ptbxl_database.csv`, sprawdzenie liczby rekordów, rozkładu 5 nadklas (NORM, MI, STTC, CD, HYP), `patient_id`, braków danych | `notebooks/01_explore_ptbxl.ipynb` |
| 2.5 | Eksploracja Chapman-Shaoxing | Wczytanie metadanych, sprawdzenie klas wspólnych z PTB-XL (NORM, AF, CD), rozkład | `notebooks/02_explore_chapman.ipynb` |
| 2.6 | Raport weryfikacyjny | Liczba rekordów, rozkład klas, brakujące dane, zgodność licencji (CC BY 4.0) | `docs/verification_report.md` |

**Kryterium zaliczenia:** Wczytanie ≥100 sygnałów; wydrukowany rozkład klas dla 5 nadklas

---

## Etap 3 – Przygotowanie Środowiska Obliczeniowego

**Cel:** Działające środowisko Python z GPU

| Lp | Zadanie | Opis | Plik wynikowy |
|---|---|---|---|
| 3.1 | Inicjalizacja repozytorium Git | `git init`, pierwszy commit z obecnym kodem (`ecg_loader/`, `DATA_PROCESSING_PLAN.md`, `ecg_exploration.ipynb`) | Repozytorium na GitHub/GitLab |
| 3.2 | Struktura katalogów | Utworzenie: `data/`, `models/`, `experiments/`, `results/`, `notebooks/`, `docs/`, `scripts/` | Drzewo katalogów |
| 3.3 | Środowisko Conda | `conda create -n ecg-trust python=3.11` | |
| 3.4 | Instalacja zależności | PyTorch 2.x z GPU, scikit-learn, wfdb, shap, lime, captum, grad-cam, netcal, mapie, pandas, numpy, scipy, matplotlib, seaborn, jupyter | |
| 3.5 | `requirements.txt` | Eksport zamrożonych wersji: `pip freeze > requirements.txt` | `requirements.txt` |
| 3.6 | `README.md` | Instrukcja: setup środowiska, struktura repo, uruchomienie | `README.md` |
| 3.7 | `scripts/setup_env.ps1` | Automatyczny skrypt tworzący środowisko i instalujący zależności | `scripts/setup_env.ps1` |
| 3.8 | Skrypt testowy CNN | Implementacja prostego CNN (np. Lightweight CNN z [11]) na 5-sekundowych wycinkach PTB-XL, trening 1 epoka | `scripts/test_cnn.py` |

**Kryterium zaliczenia:** Skrypt treningu prostego CNN kończy się bez błędów

---

## Uwagi i ryzyka

1. **PTB-XL** (21 801 nagrań, ~3.18 GB) i **Chapman-Shaoxing** (45 152 nagrań, ~5.46 GB) – pobieranie z PhysioNet może wymagać czasu i stabilnego łącza.
2. **INCART** – obecnie wczytany tylko 417 próbek/record (`MAX_SAMPLES=417` w `config.py`). Dla pełnego testu domain shift może być potrzebna zmiana limitu.
3. **Zgodność klas** między zbiorami: Chapman-Shaoxing nie zawiera klasy MI – analiza domain shift ograniczona do wspólnych klas NORM, AF, CD.
4. **Sprawdzić `OldProject/`** – może zawierać już gotowe elementy.
5. **GPU** – kluczowe dla Etapu 7+. Upewnić się, że CUDA jest dostępna przed Etapem 3.
6. **Priorytetowa literatura:** [6] PTB-XL, [15] Temperature Scaling, [16] Domain Generalization, [1] cross-dataset, [2] Conformal Prediction, [11] Lightweight CNN, [13] TS+CP ICML 2025.

---

## Podział zadań (Etapy 4-15 w skrócie)

| Etap | Opis | Kryterium |
|---|---|---|
| 4 | Eksploracyjna Analiza Danych (EDA) | Identyfikacja ≥3 różnic między PTB-XL a Chapman-Shaoxing |
| 5 | Przygotowanie zbiorów train/val/test | Zero wspólnych `patient_id` między train/val/test |
| 6 | Implementacja modeli bazowych (LR, RF, XGBoost) | Macro-AUROC ≥ 0.75 dla ≥1 modelu |
| 7 | Implementacja modeli głównych (1D-ResNet, Transformer) | Macro-AUROC na walidacji ≥ 0.85 |
| 8 | Ocena skuteczności klasyfikacji | Kompletna tabela z 6 modelami i 5 metrykami |
| 9 | Ocena kalibracji i niepewności | Reliability Diagram pokazuje poprawę po Temperature Scaling |
| 10 | Analiza wyjaśnialności | Wyjaśnienia dla ≥3 modeli; test stabilności Spearman r |
| 11 | Test odporności na zakłócenia | Tabela Robustness Drop dla ≥2 modeli i 3 poziomów szumu |
| 12 | Test uogólnienia na danych zewnętrznych | Raport domain shift drop dla 3 modeli; próba OOD detection |
| 13 | Analiza błędów | ≥10 opisanych przypadków błędnych predykcji |
| 14 | Repozytorium kodu i dokumentacja | Reprodukcja pełnego eksperymentu baseline przez osobę trzecią |
| 15 | Przygotowanie wyników do publikacji | Akceptacja szkicu artykułu przez prowadzącego |
