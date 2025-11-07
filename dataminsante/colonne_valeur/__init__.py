# -*- coding: utf-8 -*-
"""
Package : dataminsante.colonne_valeur
-------------------------------------
Ce sous-package contient les fonctions de nettoyage, de vérification et de
standardisation des noms de colonnes des fichiers Excel de surveillance
épidémiologique (Rougeole, Choléra, etc.).

Module inclus :
- colonne_nettoyage : standardisation, mapping, reclassification
"""

import logging
from pathlib import Path

# Configuration du logger local
logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

# Import des fonctions principales depuis colonne_nettoyage
from .colonne_nettoyage import (
    verifier_colonnes,
    standardiser_nom,
    renommer_colonnes_selon_mapping,
    standardiser_noms_colonnes,
    reclasser_colonnes,
    clean_all_column_names,
)

# Définir un alias du chemin de mapping par défaut pour simplifier les imports
BASE_DIR = Path(__file__).resolve().parents[2]
MAPPING_FILE_PATH = BASE_DIR / "data" / "Rename_columns.xlsx"

__all__ = [
    "verifier_colonnes",
    "standardiser_nom",
    "renommer_colonnes_selon_mapping",
    "standardiser_noms_colonnes",
    "reclasser_colonnes",
    "clean_all_column_names",
    "MAPPING_FILE_PATH",
]
