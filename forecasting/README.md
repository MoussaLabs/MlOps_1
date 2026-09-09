# Forecasting — le pipeline pas à pas

Reprise du notebook `notebooks/foodcast.ipynb`, découpé en 6 notebooks courts,
un par étape du pipeline. Chaque notebook est **autonome** : il commence par
re-construire ce dont il a besoin à partir des étapes précédentes, puis se
concentre sur sa propre étape avec des explications détaillées.

| # | Notebook | Étape | Ce qu'on produit |
|---|----------|-------|------------------|
| 1 | `01_chargement_nettoyage.ipynb` | ETL | `df` : chiffre d'affaires horaire, propre |
| 2 | `02_feature_engineering_offline.ipynb` | Features (entraînement) | `x_train`, `y_train` |
| 3 | `03_entrainement_modele.ipynb` | Modèle + validation croisée temporelle | `simple_model` entraîné |
| 4 | `04_feature_engineering_online.ipynb` | Features (prédiction) | `future` (semaine à prédire) |
| 5 | `05_prevision_visualisation.ipynb` | Prévision | `y_pred` + graphe |
| 6 | `06_incertitudes_multimodel.ipynb` | Incertitude par bootstrap | `MultiModel` + plage de prévision |

## Comment lancer

1. Ouvrir les notebooks dans l'ordre, avec le kernel **`foodcast`**.
2. Exécuter les cellules de haut en bas.

Les notebooks utilisent `sys.path.append('..')` pour importer le package
`foodcast` situé à la racine du projet.

## Données utilisées

- Jeu d'entraînement : semaines **197 à 200**
- Semaine passée pour le lag online (`past`) : semaine **200**
- Semaine prédite : la semaine qui suit (début novembre 2018)

## Étape suivante

Une fois ces 6 étapes maîtrisées : `notebooks/mlflow_tracking.ipynb`
(tracking, reproductibilité, packaging du modèle avec MLflow).
