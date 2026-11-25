"""Модуль visualization: графіки для перевірки гіпотез.

Читає очищені дані з data/processed/ (результат data_quality_analysis.py)
і зберігає графіки у reports/figures/.
"""
import matplotlib

matplotlib.use("Agg")  # лише зберігаємо файли, вікна не відкриваємо

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import MaxNLocator

from config import FIGURES_DIR, PROCESSED_DATA_PATH

SPEED = "SpeedOfTrafficInTheShelter"
LVIV = "Львівська"
MIN_INSTITUTIONS = 10

# Кольори: один колір для однієї серії, фіксований порядок для категорій
SERIES = "#257de0"
CATEGORICAL = ["#257de0", "#f47230", "#00b894", "#f2a600"]
NEUTRAL = "#b5b5b5"
INK = "#191919"
INK_SECONDARY = "#666666"
GRID = "#e7e7e7"
AXIS = "#c2c2c2"

KIND_ORDER = ["школа", "дошкільний заклад", "позашкільний заклад"]
SHELTER_ORDER = ["власне", "орендоване", "власне та орендоване", "відсутнє", "не вказано"]

plt.rcParams.update({
    "font.size": 11,
    "axes.edgecolor": AXIS,
    "axes.labelcolor": INK_SECONDARY,
    "axes.titlecolor": INK,
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
    "axes.titlelocation": "left",
    "xtick.color": INK_SECONDARY,
    "ytick.color": INK_SECONDARY,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 150,
    "savefig.bbox": "tight",
})


def load_processed() -> pd.DataFrame:
    df = pd.read_csv(PROCESSED_DATA_PATH)
    print(f"Завантажено очищені дані. Закладів: {len(df)}")
    return df


def save(fig: plt.Figure, name: str) -> None:
    path = FIGURES_DIR / name
    fig.savefig(path)
    plt.close(fig)
    print(f"Збережено: {path}")


def internet_share(df: pd.DataFrame) -> pd.Series:
    return df["InternetInShelter"].eq("так")


def plot_internet_by_kind(df: pd.DataFrame) -> None:
    """H1: частка закладів з інтернетом в укритті за типом закладу."""
    share = internet_share(df).groupby(df["InstitutionKind"]).mean().mul(100).reindex(KIND_ORDER)

    fig, ax = plt.subplots(figsize=(8, 3.2))
    bars = ax.barh(share.index, share.values, color=SERIES, height=0.55)
    ax.invert_yaxis()
    ax.bar_label(bars, labels=[f"{v:.1f}%" for v in share.values], padding=4, color=INK)
    ax.set_xlim(0, 100)
    ax.set_xlabel("Частка закладів з інтернетом в укритті, %")
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_title("Інтернет в укриттях найчастіше є у школах")
    save(fig, "internet_by_institution_kind.png")


def plot_shelter_type_by_kind(df: pd.DataFrame) -> None:
    """H1: тип укриття (власне / орендоване) за типом закладу."""
    table = (
        pd.crosstab(df["InstitutionKind"], df["AvailabilityOfShelter"], normalize="index")
        .mul(100)
        .reindex(index=KIND_ORDER, columns=SHELTER_ORDER, fill_value=0)
    )
    colors = CATEGORICAL + [NEUTRAL]

    fig, ax = plt.subplots(figsize=(9, 3.6))
    left = pd.Series(0.0, index=table.index)
    for column, color in zip(SHELTER_ORDER, colors):
        values = table[column]
        bars = ax.barh(table.index, values, left=left, color=color, height=0.55,
                       edgecolor="white", linewidth=1.5, label=column)
        text_color = "#0b0b0b" if color in ("#f2a600", NEUTRAL) else "white"
        labels = [f"{v:.0f}%" if v >= 8 else "" for v in values]
        ax.bar_label(bars, labels=labels, label_type="center", color=text_color, fontsize=10)
        left += values
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel("Частка закладів, %")
    ax.legend(ncol=5, loc="upper left", bbox_to_anchor=(0, -0.2), frameon=False,
              fontsize=9, labelcolor=INK_SECONDARY)
    ax.set_title("Тип укриття за типом закладу")
    save(fig, "shelter_type_by_institution_kind.png")


def plot_community_distribution(df: pd.DataFrame) -> None:
    """H2: розподіл громад за часткою укриттів з інтернетом."""
    by_community = (
        df.assign(internet=internet_share(df))
        .groupby("Community")
        .agg(institutions=("School", "size"), share=("internet", "mean"))
    )
    by_community["share"] *= 100
    compared = by_community[by_community["institutions"] >= MIN_INSTITUTIONS]
    oblast = internet_share(df).mean() * 100
    lviv = by_community.loc[LVIV, "share"]

    fig, ax = plt.subplots(figsize=(9, 4.2))
    ax.hist(compared["share"], bins=range(0, 105, 5), color=SERIES, edgecolor="white", linewidth=1.5)
    ax.axvline(oblast, color=INK, linestyle="--", linewidth=1.5)
    ax.axvline(lviv, color=INK_SECONDARY, linestyle=":", linewidth=1.5)
    top = ax.get_ylim()[1]
    ax.text(oblast + 0.8, top * 0.7, f"середнє\nпо області\n{oblast:.1f}%",
            color=INK, fontsize=9, va="top")
    ax.text(lviv - 0.8, top * 0.7, f"Львівська\nгромада\n{lviv:.1f}%",
            color=INK_SECONDARY, fontsize=9, va="top", ha="right")
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_xlim(0, 100)
    ax.set_xlabel("Частка закладів громади з інтернетом в укритті, %")
    ax.set_ylabel("Кількість громад")
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_title(f"Громади дуже різні: від 0% до 100% ({len(compared)} громад, ≥{MIN_INSTITUTIONS} закладів)")
    save(fig, "community_internet_share.png")


def plot_speed(df: pd.DataFrame) -> None:
    """H3: середня швидкість інтернету за формою власності та Wi-Fi."""
    speed = df.dropna(subset=[SPEED])
    by_ownership = speed.groupby("Ownership")[SPEED].agg(["mean", "count"])
    by_ownership = by_ownership.reindex(["Приватна", "Комунальна", "Державна"])
    by_wifi = (
        speed[speed["Wi-FiInShelter"] != "не вказано"]
        .groupby("Wi-FiInShelter")[SPEED].agg(["mean", "count"])
        .reindex(["так", "частково", "ні"])
    )

    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), sharey=True)
    panels = [
        (axes[0], by_ownership, "Форма власності"),
        (axes[1], by_wifi, "Wi-Fi в укритті"),
    ]
    for ax, data, title in panels:
        bars = ax.bar(data.index, data["mean"], color=SERIES, width=0.55)
        labels = [f"{m:.0f}\n(n={n})" for m, n in zip(data["mean"], data["count"])]
        ax.bar_label(bars, labels=labels, padding=3, color=INK, fontsize=9)
        ax.set_title(title, fontsize=11)
        ax.grid(axis="y", color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
    axes[0].set_ylabel("Середня швидкість, Мбіт/с")
    axes[0].set_ylim(0, by_ownership["mean"].max() * 1.3)
    fig.suptitle("Швидкість інтернету в укритті вища у приватних закладах і з Wi-Fi",
                 x=0.06, y=1.04, ha="left", fontsize=13, fontweight="bold", color=INK)
    save(fig, "speed_by_ownership_and_wifi.png")


def main() -> None:
    df = load_processed()
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    plot_internet_by_kind(df)
    plot_shelter_type_by_kind(df)
    plot_community_distribution(df)
    plot_speed(df)
    print("\nВізуалізацію завершено.")


if __name__ == "__main__":
    main()
