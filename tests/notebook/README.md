# Notebooks d'exploration

Phase exploratoire sur les fichiers de `data/batchs/` uniquement, avant la
construction du modele de prevision du chiffre d'affaires horaire (`cash_in`).

Ce sont de simples scripts Python (style jupytext) a lancer directement :

| Fichier | Contenu |
|---|---|
| `notebook_exploration.py` | Coup d'oeil rapide sur un seul batch. |
| `exploration_ventes.py` | Ventes brutes : structure, colonnes, valeurs manquantes, doublons, articles, couverture temporelle des deux restaurants, montant par commande. |
| `exploration_serie_cible.py` | Serie cible `cash_in` horaire : tendance hebdomadaire, trous de collecte, saisonnalite (heure / jour), lien avec la semaine precedente (feature `lag_1W`). Genere des figures dans `figures/`. |

```bash
python3 tests/notebook/exploration_ventes.py
python3 tests/notebook/exploration_serie_cible.py
```

Dependances : `pandas`, `numpy`, `matplotlib`.

## Points a retenir pour le modele

- **restaurant_1** nomme la colonne identifiant `Order Number`, **restaurant_2**
  `Order ID` : il faut harmoniser au chargement.
- Les batchs ne couvrent pas toutes les semaines : la serie a des trous
  (jusqu'a ~180 jours). Un lag d'une semaine n'a de sens qu'a l'interieur d'un
  bloc continu.
- ~82 % des heures sont a 0 (restaurant ferme). Le signal utile est concentre
  sur 16 h - 22 h, avec un pic vers 18 h - 19 h.
- Saisonnalite hebdomadaire nette : vendredi et samedi bien au-dessus.
- Correlation `cash_in(t)` vs `cash_in(t - 7 jours)` ~ 0,44 sur les heures
  d'ouverture : le lag hebdomadaire est informatif mais loin de tout expliquer.
