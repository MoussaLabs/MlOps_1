from pathlib import Path

import pandas as pd

# Chemin robuste vers le CSV, quel que soit le repertoire de travail.
DATA_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "batchs"
    / "restaurant_1_week_002.csv"
)

df = pd.read_csv(DATA_PATH, parse_dates=["Order Date"])

print(df.head())
print(df.shape)
print(df.dtypes)
