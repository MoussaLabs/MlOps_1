# concat/ — concatenation des batchs & CA hebdomadaire

Objectif : rassembler **tous** les CSV de `data/batchs/` en une seule table,
puis produire la representation du **chiffre d'affaires en fonction du temps,
a la semaine**.

## Lancer

```bash
python3 tests/notebook/concat/concat_batchs.py
```

Dependances : `pandas`, `matplotlib`.

## Schema different entre restaurants — comment c'est gere

| Restaurant   | Colonne identifiant | Autres colonnes |
|--------------|---------------------|-----------------|
| restaurant_1 | `Order Number`      | identiques      |
| restaurant_2 | `Order ID`          | identiques      |

Harmonisation au chargement (`concat_batchs.py`) :

1. noms de colonnes normalises (minuscule, `_`) ;
2. la colonne identifiant est renommee en `order_id` via un **mapping
   explicite** `ORDER_ID_ALIASES` — il suffit d'y ajouter une entree pour
   integrer un `restaurant_3` au schema encore different ;
3. on ne conserve que le **schema canonique** commun
   (`order_id, order_date, item_name, quantity, product_price, total_products`) ;
4. ajout de `restaurant`, `batch_week`, `source_file`, puis `pd.concat`.

`Total products` = nombre de lignes de la commande, **pas** un montant.
Le CA est recalcule : `line_total = quantity * product_price`.

## CA hebdomadaire

Agregation sur `order_date` (vraie date), pas sur le numero de batch :
`resample("W-MON")` → semaine calendaire lundi→dimanche.

Les batchs ne couvrent pas toutes les semaines. Une semaine **sans aucune
ligne collectee** est un trou de collecte : elle est marquee `NaN` (et non 0)
pour ne pas fausser la courbe.

## Sorties (`tests/notebook/concat/`)

| Fichier | Contenu |
|---|---|
| `output/ventes_concat.csv` | toutes les lignes harmonisees + `line_total` |
| `output/ca_hebdo.csv` | format long : `semaine, restaurant, ca, lignes` (avec `restaurant = "total"`) |
| `output/ca_hebdo_pivot.csv` | format large : une colonne par restaurant + `total` |
| `figures/ca_hebdo.png` | CA hebdomadaire en fonction du temps |
