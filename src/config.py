"""Спільні налаштування проєкту: джерело даних і шляхи до файлів."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Пряме посилання на CSV: «Забезпеченість укриттями закладів освіти та наявність
# в них доступу до мережі інтернет» (data.loda.gov.ua)
DATA_URL = "https://data.loda.gov.ua/dataset/6d4e06f5-f065-4010-8fbe-d911406d44d8/resource/e560f42b-a323-4676-95e5-48cef258c24e/download/2kv2026_shelter_internet.csv"

RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "dataset.csv"
# Резервна копія набору: використовується, лише якщо портал недоступний
# і ввімкнено змінну середовища DATA_LOAD_FALLBACK=1 (так робить CI)
FALLBACK_DATA_PATH = PROJECT_ROOT / "data" / "fallback" / "dataset.csv"
PROCESSED_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "dataset_clean.csv"
FIGURES_DIR = PROJECT_ROOT / "reports" / "figures"
