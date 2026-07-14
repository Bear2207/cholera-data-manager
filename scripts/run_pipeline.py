#!/usr/bin/env python3
"""Pipeline simplifié : import brut des fichiers Excel avec choix.

Usage:
  python scripts/run_pipeline.py [--ids] [--ll] [--all] [--sync-only]
  --ids    : importer uniquement les données IDS
  --ll     : importer uniquement les données LL
  --all    : importer les deux (équivaut à --ids --ll)
  --sync-only : ne faire que la synchronisation des FK (sans importer)
Si aucun argument n'est fourni, un menu interactif s'affiche.
"""
import logging
import sys
import argparse
from pathlib import Path
from sqlalchemy.dialects.postgresql import insert

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from database import get_engine
from schema import ensure_schema
from loaders.ids_loader import load_ids_excel
from loaders.ll_loader import load_ll_excel
from sync.lookup_sync import sync_ids_lookups, sync_ll_lookups

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

INSERT_CHUNKSIZE = 1000

def insert_on_conflict_do_nothing(table, conn, keys, data_iter):
    data = [dict(zip(keys, row)) for row in data_iter]
    if not data:
        return 0
    stmt = insert(table.table).values(data).on_conflict_do_nothing()
    result = conn.execute(stmt)
    return result.rowcount


def import_ids(engine):
    ids_file = Path('data/ids/IDS_2025.xlsx')
    if not ids_file.exists():
        logger.error("Fichier IDS introuvable : %s", ids_file)
        return
    logger.info("Chargement du fichier IDS : %s", ids_file)
    df = load_ids_excel(ids_file)
    # Insertion brute (pandas gère les types)
    with engine.begin() as conn:
        df.to_sql('cas_maladie', conn, schema='cholera', if_exists='append', index=False, method='multi', chunksize=INSERT_CHUNKSIZE)
    logger.info("Insertion IDS terminée : %d lignes", len(df))
    sync_ids_lookups(engine)

def import_ll(engine):
    ll_files = list(Path('data/ll').glob('rdc_compilation*_LL_Cholera_*.xlsx'))
    if not ll_files:
        logger.error("Aucun fichier LL trouvé dans data/ll/")
        return
    for f in ll_files:
        logger.info("Chargement du fichier LL : %s", f)
        df = load_ll_excel(f)
        with engine.begin() as conn:
            df.to_sql('cas_ll', conn, schema='cholera', if_exists='append', index=False, method=insert_on_conflict_do_nothing, chunksize=INSERT_CHUNKSIZE)
        logger.info("Insertion LL terminée : %d lignes depuis %s", len(df), f.name)
    sync_ll_lookups(engine)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ids', action='store_true', help="Importer les données IDS")
    parser.add_argument('--ll', action='store_true', help="Importer les données LL")
    parser.add_argument('--all', action='store_true', help="Importer les deux (IDS et LL)")
    parser.add_argument('--sync-only', action='store_true', help="Synchroniser les clés étrangères sans importer")
    args = parser.parse_args()

    engine = get_engine()
    ensure_schema(engine)

    # Déterminer ce qu'on doit faire
    if args.sync_only:
        logger.info("Mode synchronisation uniquement")
        # On synchronise les deux
        sync_ids_lookups(engine)
        sync_ll_lookups(engine)
        return

    if args.all:
        import_ids(engine)
        import_ll(engine)
        return

    if args.ids:
        import_ids(engine)
        return

    if args.ll:
        import_ll(engine)
        return

    # Aucun argument : menu interactif
    print("\n=== Cholera Data Manager ===\n")
    print("1. Importer les données IDS")
    print("2. Importer les données LL")
    print("3. Importer les deux (IDS + LL)")
    print("4. Synchroniser les clés étrangères (sans importer)")
    print("5. Quitter")
    choice = input("Votre choix (1-5) : ").strip()
    if choice == '1':
        import_ids(engine)
    elif choice == '2':
        import_ll(engine)
    elif choice == '3':
        import_ids(engine)
        import_ll(engine)
    elif choice == '4':
        sync_ids_lookups(engine)
        sync_ll_lookups(engine)
    else:
        print("Au revoir.")

if __name__ == '__main__':
    main()