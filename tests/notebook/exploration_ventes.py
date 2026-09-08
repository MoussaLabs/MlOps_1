"""
Exploration des ventes brutes (dossier data/batchs uniquement).

But : comprendre la matiere premiere avant de construire un modele de
prevision du chiffre d'affaires. On regarde ici la structure des commandes,
les valeurs manquantes, les articles et la couverture temporelle.

Lancer :  python3 tests/notebook/exploration_ventes.py
"""
from pathlib import Path

import pandas as pd

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 200)

BATCHS_DIR = Path(__file__).resolve().parents[2] / "data" / "batchs"


def load_batchs(prefix: str) -> pd.DataFrame:
    """Concatene tous les CSV hebdomadaires d'un restaurant du dossier batchs."""
    frames = []
    for path in sorted(BATCHS_DIR.glob(f"{prefix}_week_*.csv")):
        week = int(path.stem.split("_week_")[1])
        batch = pd.read_csv(path, parse_dates=["Order Date"])
        batch["week"] = week
        batch["restaurant"] = prefix
        frames.append(batch)
    df = pd.concat(frames, ignore_index=True)
    df.columns = df.columns.str.lower().str.replace(" ", "_")
    # restaurant_1 nomme la colonne "Order Number", restaurant_2 "Order ID".
    df = df.rename(columns={"order_number": "order_id"})
    return df


df = pd.concat([load_batchs("restaurant_1"), load_batchs("restaurant_2")], ignore_index=True)

print("=== Apercu ===")
print(df.head())

print("\n=== Colonnes reellement presentes dans les CSV ===")
for prefix in ("restaurant_1", "restaurant_2"):
    sample = next((BATCHS_DIR).glob(f"{prefix}_week_*.csv"))
    print(prefix, "->", list(pd.read_csv(sample, nrows=0).columns))

print("\n=== Dimensions et types ===")
print(df.shape)
print(df.dtypes)

print("\n=== Valeurs manquantes ===")
print(df.isna().sum())

print("\n=== Doublons de lignes ===")
print(df.duplicated().sum())

print("\n=== Couverture temporelle par restaurant ===")
print(
    df.groupby("restaurant").agg(
        semaines=("week", "nunique"),
        premiere_commande=("order_date", "min"),
        derniere_commande=("order_date", "max"),
        lignes=("order_date", "size"),
        commandes=("order_id", "nunique"),
    )
)

print("\n=== Statistiques des colonnes numeriques ===")
print(df[["quantity", "product_price", "total_products"]].describe())

print("\n=== Top 10 des articles les plus vendus (quantite) ===")
print(df.groupby("item_name")["quantity"].sum().sort_values(ascending=False).head(10))

# Panier : chiffre d'affaires par commande = somme(quantite * prix unitaire).
df["line_total"] = df["quantity"] * df["product_price"]
orders = df.groupby(["restaurant", "order_id", "order_date"], as_index=False)["line_total"].sum()
orders = orders.rename(columns={"line_total": "cash_in"})

print("\n=== Distribution du montant par commande ===")
print(orders.groupby("restaurant")["cash_in"].describe())
