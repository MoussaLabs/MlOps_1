"""
Concatenation de tous les CSV de data/batchs/ et calcul du chiffre d'affaires
hebdomadaire (par restaurant + total).

Probleme : le schema differe entre restaurants.
    restaurant_1 -> colonne identifiant "Order Number"
    restaurant_2 -> colonne identifiant "Order ID"
Le reste des colonnes est identique :
    Order Date, Item Name, Quantity, Product Price, Total products
"Total products" = nombre de lignes de la commande (PAS un montant).
Le chiffre d'affaires d'une ligne = Quantity * Product Price.

Solution d'harmonisation :
    1. on normalise les noms de colonnes (minuscule, "_")
    2. on renomme l'identifiant de commande en "order_id" quel que soit le
       nom d'origine (mapping explicite, extensible a d'autres restaurants)
    3. on ne garde qu'un socle de colonnes commun ("schema canonique")
    4. on ajoute restaurant + numero de batch, puis on concatene

Le CA hebdomadaire est calcule a partir de "Order Date" (vraie date), pas du
numero de batch : on resample par semaine calendaire (lundi -> dimanche).

Lancer :  python3 tests/notebook/concat/concat_batchs.py

Sorties (dans tests/notebook/concat/) :
    output/ventes_concat.csv  -> toutes les lignes harmonisees + line_total
    output/ca_hebdo.csv       -> CA par semaine et par restaurant (format long)
    output/ca_hebdo_pivot.csv -> CA par semaine, une colonne par restaurant
    figures/ca_hebdo.png      -> CA hebdomadaire en fonction du temps
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
BATCHS_DIR = ROOT / "data" / "batchs"
HERE = Path(__file__).resolve().parent
OUTPUT_DIR = HERE / "output"
FIGURES_DIR = HERE / "figures"
OUTPUT_DIR.mkdir(exist_ok=True)
FIGURES_DIR.mkdir(exist_ok=True)

# Schema canonique attendu apres harmonisation.
CANONICAL_COLUMNS = [
    "order_id",
    "order_date",
    "item_name",
    "quantity",
    "product_price",
    "total_products",
]

# Noms possibles de la colonne "identifiant de commande" selon le restaurant.
ORDER_ID_ALIASES = {
    "order_number": "order_id",  # restaurant_1
    "order_id": "order_id",      # restaurant_2
}


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """minuscule + underscores, puis unification de l'identifiant de commande."""
    df = df.copy()
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    df = df.rename(columns=ORDER_ID_ALIASES)
    return df


def load_one_batch(path: Path) -> pd.DataFrame:
    """Charge un CSV hebdomadaire et le ramene au schema canonique."""
    restaurant, week = path.stem.split("_week_")
    raw = pd.read_csv(path, parse_dates=["Order Date"])
    df = normalize_columns(raw)

    missing = set(CANONICAL_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"{path.name}: colonnes manquantes {sorted(missing)}")

    df = df[CANONICAL_COLUMNS].copy()
    df["restaurant"] = restaurant
    df["batch_week"] = int(week)
    df["source_file"] = path.name
    return df


def load_all_batchs() -> pd.DataFrame:
    """Concatene tous les CSV de data/batchs/, tous restaurants confondus."""
    paths = sorted(BATCHS_DIR.glob("*.csv"))
    if not paths:
        raise FileNotFoundError(f"Aucun CSV dans {BATCHS_DIR}")
    frames = [load_one_batch(p) for p in paths]
    df = pd.concat(frames, ignore_index=True)

    # Nettoyage minimal.
    before = len(df)
    df = df.dropna(subset=["order_date", "quantity", "product_price"])
    df = df.drop_duplicates(
        subset=["restaurant", "order_id", "order_date", "item_name",
                "quantity", "product_price"]
    )
    print(f"Lignes chargees : {before} -> {len(df)} apres nettoyage/dedup")

    # Chiffre d'affaires par ligne de commande.
    df["line_total"] = df["quantity"] * df["product_price"]
    return df.sort_values("order_date").reset_index(drop=True)


def chiffre_affaires_hebdo(df: pd.DataFrame) -> pd.DataFrame:
    """CA agrege par semaine calendaire (lundi) et par restaurant, format long.

    Les batchs ne couvrent pas toutes les semaines. Une semaine sans aucune
    ligne collectee est un TROU de collecte, pas un CA nul : on la marque NaN
    pour ne pas fausser la representation temporelle.
    """
    grouped = (
        df.set_index("order_date")
        .groupby("restaurant")["line_total"]
        .resample("W-MON", label="left", closed="left")
    )
    weekly = grouped.agg(ca="sum", lignes="size").reset_index()
    weekly = weekly.rename(columns={"order_date": "semaine"})
    weekly.loc[weekly["lignes"] == 0, "ca"] = pd.NA

    total = (
        weekly.groupby("semaine", as_index=False)
        .agg(ca=("ca", "sum"), lignes=("lignes", "sum"))
        .assign(restaurant="total")
    )
    total.loc[total["lignes"] == 0, "ca"] = pd.NA

    weekly = pd.concat([weekly, total], ignore_index=True)
    return weekly.sort_values(["restaurant", "semaine"]).reset_index(drop=True)


def plot_ca_hebdo(weekly: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(14, 6))
    for restaurant, grp in weekly.groupby("restaurant"):
        style = dict(lw=2.2, color="black") if restaurant == "total" else dict(lw=1.3)
        ax.plot(grp["semaine"], grp["ca"], label=restaurant, **style)
    ax.set_title("Chiffre d'affaires hebdomadaire par restaurant")
    ax.set_xlabel("Semaine")
    ax.set_ylabel("CA (somme quantite x prix)")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def main() -> None:
    df = load_all_batchs()

    print("\n=== Apercu des ventes concatenees ===")
    print(df.head())
    print("\nDimensions :", df.shape)
    print("\nCouverture temporelle :")
    print(
        df.groupby("restaurant").agg(
            premiere_commande=("order_date", "min"),
            derniere_commande=("order_date", "max"),
            lignes=("order_date", "size"),
            commandes=("order_id", "nunique"),
            batchs=("batch_week", "nunique"),
            ca_total=("line_total", "sum"),
        )
    )

    weekly = chiffre_affaires_hebdo(df)
    pivot = (
        weekly.pivot(index="semaine", columns="restaurant", values="ca")
        .sort_index()
    )

    print("\n=== CA hebdomadaire (dernieres semaines) ===")
    print(pivot.tail(10))

    ventes_path = OUTPUT_DIR / "ventes_concat.csv"
    ca_long_path = OUTPUT_DIR / "ca_hebdo.csv"
    ca_pivot_path = OUTPUT_DIR / "ca_hebdo_pivot.csv"
    fig_path = FIGURES_DIR / "ca_hebdo.png"

    df.to_csv(ventes_path, index=False)
    weekly.to_csv(ca_long_path, index=False)
    pivot.to_csv(ca_pivot_path)
    plot_ca_hebdo(weekly, fig_path)

    print("\nFichiers ecrits :")
    for p in (ventes_path, ca_long_path, ca_pivot_path, fig_path):
        print("  -", p.relative_to(ROOT))


if __name__ == "__main__":
    main()
