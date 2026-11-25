"""Модуль data_research: перевірка гіпотез і проста модель.

Читає очищені дані з data/processed/ (результат data_quality_analysis.py),
перевіряє три гіпотези з README та будує модель логістичної регресії.
"""
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split

from config import PROCESSED_DATA_PATH

SPEED = "SpeedOfTrafficInTheShelter"
LVIV = "Львівська"
MIN_INSTITUTIONS = 10  # громади з меншою кількістю закладів не порівнюємо
RANDOM_STATE = 42


def load_processed() -> pd.DataFrame:
    df = pd.read_csv(PROCESSED_DATA_PATH)
    print(f"Завантажено очищені дані. Закладів: {len(df)}, громад: {df['Community'].nunique()}")
    return df


def has_internet(df: pd.DataFrame) -> pd.Series:
    return df["InternetInShelter"].eq("так")


def verdict(confirmed: bool) -> str:
    return "ПІДТВЕРДЖУЄТЬСЯ" if confirmed else "НЕ ПІДТВЕРДЖУЄТЬСЯ"


def hypothesis_1(df: pd.DataFrame) -> None:
    """Тип закладу та інтернет в укритті."""
    print("\n" + "=" * 70)
    print("[H1] Тип закладу та інтернет в укритті")

    share = has_internet(df).groupby(df["InstitutionKind"]).mean().mul(100).round(1)
    print("\nЧастка закладів з інтернетом в укритті, %:")
    print(share.sort_values(ascending=False).to_string())

    shelter = pd.crosstab(df["InstitutionKind"], df["AvailabilityOfShelter"], normalize="index")
    print("\nТип укриття за типом закладу, %:")
    print(shelter.mul(100).round(1).to_string())

    schools = share["школа"]
    others = share.drop("школа")
    print(f"\nГіпотеза «у школах інтернет в укриттях є частіше»: {verdict(bool((schools > others).all()))}")


def hypothesis_2(df: pd.DataFrame) -> None:
    """Нерівність між громадами."""
    print("\n" + "=" * 70)
    print("[H2] Частка укриттів з інтернетом у громадах")

    by_community = (
        df.assign(internet=has_internet(df))
        .groupby("Community")
        .agg(institutions=("School", "size"), internet_share=("internet", "mean"))
    )
    by_community["internet_share"] = by_community["internet_share"].mul(100).round(1)
    compared = by_community[by_community["institutions"] >= MIN_INSTITUTIONS]

    print(f"\nГромад із щонайменше {MIN_INSTITUTIONS} закладами: {len(compared)} з {len(by_community)}")
    print(compared["internet_share"].describe().round(1).to_string())

    ranked = compared.sort_values("internet_share")
    print("\n5 громад з найнижчою часткою:")
    print(ranked.head(5).to_string())
    print("\n5 громад з найвищою часткою:")
    print(ranked.tail(5).to_string())

    gap = compared["internet_share"].max() - compared["internet_share"].min()
    oblast = round(has_internet(df).mean() * 100, 1)
    lviv = by_community.loc[LVIV, "internet_share"]
    print(f"\nРозрив між громадами: {gap:.1f} в.п.")
    print(f"Середнє по області: {oblast}%, Львівська громада: {lviv}%")
    print(f"Гіпотеза «розрив значний (> 30 в.п.)»: {verdict(gap > 30)}")
    print(f"Гіпотеза «Львівська громада вища за середнє»: {verdict(lviv > oblast)}")


def hypothesis_3(df: pd.DataFrame) -> None:
    """Швидкість інтернету, форма власності та Wi-Fi."""
    print("\n" + "=" * 70)
    print("[H3] Швидкість інтернету в укритті, Мбіт/с")

    speed = df.dropna(subset=[SPEED])
    stats = ["mean", "median", "count"]

    by_ownership = speed.groupby("Ownership")[SPEED].agg(stats).round(1)
    print("\nЗа формою власності:")
    print(by_ownership.to_string())

    by_wifi = (
        speed[speed["Wi-FiInShelter"] != "не вказано"]
        .groupby("Wi-FiInShelter")[SPEED].agg(stats).round(1)
    )
    print("\nЗа наявністю Wi-Fi:")
    print(by_wifi.to_string())

    private_faster = by_ownership.loc["Приватна", "mean"] > by_ownership.loc["Комунальна", "mean"]
    wifi_faster = by_wifi.loc["так", "mean"] > by_wifi.loc["ні", "mean"]
    print(f"\nГіпотеза «у приватних закладах швидше»: {verdict(bool(private_faster))}")
    print(f"Гіпотеза «в укриттях з Wi-Fi швидше»: {verdict(bool(wifi_faster))}")


def build_model(df: pd.DataFrame) -> None:
    """Логістична регресія: чи буде в укритті інтернет.

    Ознаки: тип закладу, форма власності, тип укриття та розмір громади
    (кількість закладів у ній). Wi-Fi і швидкість не беремо: вони напряму
    випливають з наявності інтернету, і модель просто «підгляне» відповідь.
    """
    print("\n" + "=" * 70)
    print("[Модель] Логістична регресія: прогноз наявності інтернету в укритті")

    data = df[df["InternetInShelter"].isin(["так", "ні"])].copy()
    y = has_internet(data).astype(int)

    X = pd.get_dummies(
        data[["InstitutionKind", "Ownership", "AvailabilityOfShelter"]],
        drop_first=True,
        dtype=int,
    )
    X["CommunitySize_x100"] = data.groupby("Community")["School"].transform("size") / 100

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, stratify=y, random_state=RANDOM_STATE
    )
    model = LogisticRegression(max_iter=1000, class_weight="balanced")
    model.fit(X_train, y_train)

    predicted = model.predict(X_test)
    probability = model.predict_proba(X_test)[:, 1]
    baseline = max(y_test.mean(), 1 - y_test.mean())

    print(f"\nНавчальна вибірка: {len(X_train)}, тестова: {len(X_test)}")
    print(f"Accuracy моделі: {accuracy_score(y_test, predicted):.3f}")
    print(f"Accuracy «завжди так» (базова лінія): {baseline:.3f}")
    print(f"ROC AUC: {roc_auc_score(y_test, probability):.3f} (0.5 = випадкове вгадування)")

    coefficients = pd.Series(model.coef_[0], index=X.columns).sort_values()
    print("\nКоефіцієнти (> 0 збільшує шанс мати інтернет, < 0 зменшує):")
    print(coefficients.round(3).to_string())


def main() -> None:
    df = load_processed()
    hypothesis_1(df)
    hypothesis_2(df)
    hypothesis_3(df)
    build_model(df)
    print("\nДослідження завершено.")


if __name__ == "__main__":
    main()
