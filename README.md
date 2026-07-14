# Cholera Data Manager

Pipeline ETL pour importer les données Excel (IDS et LL Choléra) dans une base PostgreSQL/PostGIS.

## Prérequis

- Docker & Docker Compose
- Python 3.9+
- Fichiers Excel placés dans `data/ids/` et `data/ll/`

## Installation

1. Copier `.env.example` vers `.env` et ajuster si nécessaire.
2. Lancer les services : `docker compose up -d`
3. Installer les dépendances Python : `pip install -r requirements.txt`

## Utilisation

- Lancer le pipeline complet : `python scripts/run_pipeline.py --all`
- Importer seulement IDS : `python scripts/run_pipeline.py --ids`
- Importer seulement LL : `python scripts/run_pipeline.py --ll`
- Synchroniser seulement les clés étrangères : `python scripts/run_pipeline.py --sync-only`
- Vérifier les données : `python scripts/check_data.py`

## Structure

- `src/` : code modulaire (loaders, sync, utilitaires)
- `scripts/` : points d'entrée
- `db/` : schéma SQL
- `data/` : fichiers sources (ignorés par Git)
- `logs/` : journaux d'exécution

## Améliorations par rapport à la version initiale

- Schéma corrigé (contraintes, types booléens, unicité renforcée)
- Pipeline modulaire et testable
- Gestion des erreurs et logs
- Synchronisation automatique des clés étrangères
- Calcul de la létalité via vue (plus performant)
