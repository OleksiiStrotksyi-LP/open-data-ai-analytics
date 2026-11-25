"""Модуль data_quality_analysis: перевірка якості та очищення даних.

Читає сирі дані з data/raw/, друкує звіт про проблеми якості,
виправляє їх і зберігає очищений набір у data/processed/.
"""
import pandas as pd

from config import PROCESSED_DATA_PATH, RAW_DATA_PATH

SPEED = "SpeedOfTrafficInTheShelter"
TEXT_COLUMNS = [
    "Community", "School", "TypeOfInstitution", "Ownership",
    "AvailabilityOfShelter", "InternetInShelter", "Wi-FiInShelter",
]
CODE_COLUMNS = ["EDRPOU", "EDEBO", "ISUO"]
YES_NO_COLUMNS = ["InternetInShelter", "Wi-FiInShelter"]

YES_NO_VALUES = {"так", "ні", "частково"}
SHELTER_MAP = {
    "власне": "власне",
    "орендоване": "орендоване",
    "власне та орендоване": "власне та орендоване",
    "відсутнє": "відсутнє",
    "немає": "відсутнє",
}
# Позначки в TypeOfInstitution для закладів, які фактично не працюють
INACTIVE_MARKERS = ("ліквідовано", "реорганізовано", "не розпочато")
MISSING = "не вказано"


def load_raw() -> pd.DataFrame:
    df = pd.read_csv(RAW_DATA_PATH, dtype=str)
    print(f"Завантажено {RAW_DATA_PATH.name}: {len(df)} рядків, {df.shape[1]} колонок")
    return df


def quality_report(df: pd.DataFrame) -> None:
    """Друкує звіт про проблеми якості в сирих даних."""
    print("\n=== 1. Пропущені значення ===")
    missing = df.isna().sum()
    print(missing[missing > 0].to_string())

    print("\n=== 2. Дублікати ===")
    print(f"Повні дублікати рядків: {df.duplicated().sum()}")
    same_name = df.duplicated(["Community", "School"]).sum()
    same_unit = df.duplicated(["Community", "School", "TypeOfInstitution"]).sum()
    print(f"Однакова назва в межах громади: {same_name} "
          f"(школа та її дошкільний підрозділ мають одну назву, тому це не дублікати)")
    print(f"Дублікати «громада + назва + тип закладу»: {same_unit}")

    print("\n=== 3. Значення категоріальних колонок (до очищення) ===")
    for col in ["TypeOfInstitution", "Ownership", "AvailabilityOfShelter", *YES_NO_COLUMNS]:
        print(f"\n{col}:")
        print(df[col].value_counts(dropna=False).to_string())

    print(f"\n=== 4. Числова колонка {SPEED} ===")
    speed = pd.to_numeric(df[SPEED].str.replace(",", ".", regex=False), errors="coerce")
    not_numeric = df[SPEED].notna() & speed.isna()
    print(f"Нечислових значень: {not_numeric.sum()}, від'ємних: {(speed < 0).sum()}")
    print(speed.describe().round(1).to_string())


def normalize_text(series: pd.Series) -> pd.Series:
    """Прибирає зайві пробіли на краях і подвійні пробіли всередині."""
    return series.str.strip().str.replace(r"\s+", " ", regex=True)


def classify_institution(type_of_institution: str) -> str:
    """Зводить 13 варіантів TypeOfInstitution до трьох типів закладів."""
    value = type_of_institution.lower()
    if "позашкільн" in value:
        return "позашкільний заклад"
    if "дошкільн" in value:
        return "дошкільний заклад"
    if "ззсо" in value:
        return "школа"
    return "інший"


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Виправляє знайдені проблеми та друкує, що саме змінено."""
    print("\n=== Очищення даних ===")
    df = df.copy()

    for col in TEXT_COLUMNS + CODE_COLUMNS:
        df[col] = normalize_text(df[col])

    before = len(df)
    df = df.drop_duplicates()
    print(f"Видалено повних дублікатів: {before - len(df)}")

    inactive = df["TypeOfInstitution"].str.lower().str.contains("|".join(INACTIVE_MARKERS))
    print(f"Видалено ліквідованих / реорганізованих закладів: {inactive.sum()}")
    df = df[~inactive].copy()

    # «приватна» / «Приватна», «комунальна» / «Комунальна» -> одне написання
    df["Ownership"] = df["Ownership"].str.capitalize()

    df["InstitutionKind"] = df["TypeOfInstitution"].map(classify_institution)
    print("Додано колонку InstitutionKind (школа / дошкільний / позашкільний заклад)")

    shelter = df["AvailabilityOfShelter"].str.lower().map(SHELTER_MAP)
    print(f"AvailabilityOfShelter: «немає» -> «відсутнє», пропусків замінено: {shelter.isna().sum()}")
    df["AvailabilityOfShelter"] = shelter.fillna(MISSING)

    for col in YES_NO_COLUMNS:
        values = df[col].str.lower()
        invalid = values.notna() & ~values.isin(YES_NO_VALUES)
        print(f"{col}: некоректних значень (напр. «1-так. 2-ні») {invalid.sum()}, "
              f"пропусків {values.isna().sum()} -> «{MISSING}»")
        df[col] = values.where(~invalid).fillna(MISSING)

    df[SPEED] = pd.to_numeric(df[SPEED].str.replace(",", ".", regex=False), errors="coerce")
    no_internet = df["InternetInShelter"].eq("ні")
    filled = no_internet & df[SPEED].isna()
    df.loc[filled, SPEED] = 0
    print(f"{SPEED}: немає інтернету -> швидкість 0, заповнено {filled.sum()}; "
          f"невідома швидкість лишилась NaN: {df[SPEED].isna().sum()}")
    conflicts = no_internet & df[SPEED].gt(0)
    print(f"Суперечність «інтернету немає, але швидкість > 0»: {conflicts.sum()} "
          f"(лишаємо як є, бо невідомо, яке з двох полів хибне)")

    # Коди ЄДРПОУ / ЄДЕБО / ІСУО — ідентифікатори: пропуски не вигадуємо, лишаємо NaN
    print(f"Пропуски в кодах лишаються без змін: {df[CODE_COLUMNS].isna().sum().to_dict()}")

    return df.reset_index(drop=True)


def main() -> None:
    df = load_raw()
    quality_report(df)
    clean_df = clean(df)

    print("\n=== Результат ===")
    print(f"Рядків: {len(df)} -> {len(clean_df)}")
    for col in ["InstitutionKind", "Ownership", "AvailabilityOfShelter", *YES_NO_COLUMNS]:
        print(f"\n{col}:")
        print(clean_df[col].value_counts().to_string())

    PROCESSED_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    clean_df.to_csv(PROCESSED_DATA_PATH, index=False)
    print(f"\nОчищені дані збережено: {PROCESSED_DATA_PATH}")


if __name__ == "__main__":
    main()
