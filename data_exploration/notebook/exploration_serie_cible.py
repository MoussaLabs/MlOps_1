"""
Exploration de la serie cible : le chiffre d'affaires horaire ("cash_in").

C'est la variable que le modele devra prevoir. On reconstruit la meme serie
que le pipeline `foodcast` (somme des deux restaurants, pas de temps horaire),
puis on regarde la tendance, la saisonnalite et le lien avec la semaine
precedente (feature `lag_1W` du modele).

Donnees : dossier data/batchs uniquement.
Lancer  :  python3 tests/notebook/exploration_serie_cible.py
Figures :  tests/notebook/figures/
"""
from pathlib import Path

import numpy as np
import pandas as pd

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 200)

BATCHS_DIR = Path(__file__).resolve().parents[2] / "data" / "batchs"
FIG_DIR = Path(__file__).resolve().parent / "figures"
FIG_DIR.mkdir(exist_ok=True)


def hourly_cash_in() -> pd.Series:
    """Chiffre d'affaires horaire, tous restaurants confondus (data/batchs)."""
    frames = []
    for path in sorted(BATCHS_DIR.glob("restaurant_*_week_*.csv")):
        batch = pd.read_csv(path, parse_dates=["Order Date"])
        batch.columns = batch.columns.str.lower().str.replace(" ", "_")
        batch = batch.rename(columns={"order_number": "order_id"})
        frames.append(batch)
    df = pd.concat(frames, ignore_index=True).drop_duplicates()
    df["cash_in"] = df["quantity"] * df["product_price"]
    series = df.set_index("order_date")["cash_in"].sort_index()
    return series.resample("1h").sum()


cash = hourly_cash_in()

print("=== Serie horaire ===")
print(f"periode      : {cash.index.min()} -> {cash.index.max()}")
print(f"nb d'heures  : {len(cash)}")
print(f"heures a 0   : {(cash == 0).mean():.1%} (restaurant ferme)")
print(cash.describe())

# Sur les heures d'ouverture seulement (cash_in > 0), pour ne pas etre noye
# par les heures de fermeture.
ouvert = cash[cash > 0]
print("\n=== Heures d'ouverture uniquement ===")
print(ouvert.describe())

# Les batchs ne couvrent pas toutes les semaines : il y a des trous. C'est
# important pour le modele (le lag d'une semaine n'a pas de sens en travers
# d'un trou).
jours_actifs = cash.resample("1D").sum()
jours_actifs = jours_actifs[jours_actifs > 0].index
trous = jours_actifs.to_series().diff().dt.days
print("\n=== Continuite temporelle ===")
print(f"jours avec des ventes         : {len(jours_actifs)}")
print(f"plus longue coupure (jours)   : {int(trous.max())}")
print(f"nb de coupures > 2 jours      : {int((trous > 2).sum())}")

print("\n=== Tendance : chiffre d'affaires hebdomadaire (5 premieres / 5 dernieres) ===")
weekly = cash.resample("1W").sum()
weekly = weekly[weekly > 0]
print(pd.concat([weekly.head(), weekly.tail()]))

print("\n=== Saisonnalite : CA moyen par heure de la journee ===")
by_hour = cash.groupby(cash.index.hour).mean()
print(by_hour.round(1))

print("\n=== Saisonnalite : CA moyen par jour de la semaine (0=lundi) ===")
by_day = cash.groupby(cash.index.weekday).mean()
print(by_day.round(1))

# Feature cle du modele : la meme heure une semaine avant.
lag = cash.shift(24 * 7)
mask = (cash > 0) & (lag > 0)
corr = np.corrcoef(cash[mask], lag[mask])[0, 1]
print("\n=== Lien avec la semaine precedente (feature lag_1W) ===")
print(f"correlation cash_in(t) vs cash_in(t-7j), heures ouvertes : {corr:.3f}")

# --- Figures ---
fig, ax = plt.subplots(figsize=(12, 4))
weekly.plot(ax=ax)
ax.set(title="Chiffre d'affaires hebdomadaire", xlabel="date", ylabel="dollars")
fig.tight_layout()
fig.savefig(FIG_DIR / "ca_hebdomadaire.png", dpi=110)

fig, axes = plt.subplots(1, 2, figsize=(12, 4))
by_hour.plot(kind="bar", ax=axes[0], title="CA moyen par heure")
axes[0].set(xlabel="heure", ylabel="dollars")
by_day.plot(kind="bar", ax=axes[1], title="CA moyen par jour (0=lundi)")
axes[1].set(xlabel="jour", ylabel="dollars")
fig.tight_layout()
fig.savefig(FIG_DIR / "saisonnalite.png", dpi=110)

fig, ax = plt.subplots(figsize=(12, 4))
cash.loc["2018-12-10":"2019-01-07"].plot(ax=ax)
ax.set(title="Zoom : un mois de serie horaire (dec. 2018)", xlabel="date", ylabel="dollars")
fig.tight_layout()
fig.savefig(FIG_DIR / "zoom_horaire.png", dpi=110)

print(f"\nFigures enregistrees dans {FIG_DIR}")
