"""Модуль data_load: завантажує набір даних з data.gov.ua у data/raw/."""
import csv
import io
import sys
import zipfile

import pandas as pd
import requests

from config import DATA_URL, RAW_DATA_PATH

ENCODINGS = ("utf-8-sig", "cp1251")
DELIMITERS = ";,\t|"


def download(url: str) -> bytes:
    """Завантажує файл за посиланням; якщо це ZIP, повертає перший CSV з архіву."""
    print(f"Завантаження даних з {url} ...")
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    content = response.content

    if zipfile.is_zipfile(io.BytesIO(content)):
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            csv_files = [n for n in archive.namelist() if n.lower().endswith(".csv")]
            if not csv_files:
                raise ValueError("В архіві немає CSV-файлів")
            print(f"Розпаковано {csv_files[0]} з архіву")
            content = archive.read(csv_files[0])

    print(f"Отримано {len(content) / 1024:.1f} KB")
    return content


def decode(content: bytes) -> str:
    """Визначає кодування: data.gov.ua публікує файли в UTF-8 або cp1251."""
    for encoding in ENCODINGS:
        try:
            text = content.decode(encoding)
            print(f"Кодування: {encoding}")
            return text
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Не вдалося декодувати файл ({', '.join(ENCODINGS)})")


def parse_csv(text: str) -> pd.DataFrame:
    """Визначає роздільник і читає CSV у DataFrame."""
    sample = text[:10_000]
    try:
        sep = csv.Sniffer().sniff(sample, delimiters=DELIMITERS).delimiter
    except csv.Error:
        sep = ";" if sample.count(";") > sample.count(",") else ","
    print(f"Роздільник: {sep!r}")
    return pd.read_csv(io.StringIO(text), sep=sep, low_memory=False)


def main() -> None:
    if DATA_URL.startswith("PASTE"):
        sys.exit("Вкажіть DATA_URL у src/config.py")

    df = parse_csv(decode(download(DATA_URL)))

    # Зберігаємо без змін у даних, лише в єдиному форматі (UTF-8, кома)
    RAW_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(RAW_DATA_PATH, index=False)

    print(f"\nЗбережено: {RAW_DATA_PATH}")
    print(f"Рядків: {len(df)}, колонок: {df.shape[1]}\n")
    print(df.dtypes.to_string())
    print()
    print(df.head().to_string())


if __name__ == "__main__":
    main()
