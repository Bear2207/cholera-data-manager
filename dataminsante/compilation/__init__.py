# -*- coding: utf-8 -*-
"""
Package : dataminsante.compilation
----------------------------------
Ce sous-package contient les modules responsables de la lecture,
de la standardisation, du nommage et de la fusion des fichiers Excel
de surveillance épidémiologique (Rougeole, Choléra, etc.).

Modules inclus :
- fichiers_compilation : chargement, fusion, export Excel
- fichiers_nommage : gestion et validation des noms de fichiers
"""

import logging

# Initialisation d’un logger spécifique au package
logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

# Import des sous-modules principaux
from .fichiers_compilation import (
    lister_fichiers_excel,
    lire_fichiers_excel,
    charger_fichiers_excel,
    exporter_dataframe_excel,
)

from .fichiers_nommage import (
    generer_nom_fichier,
    generer_nom_feuille,
    est_nom_fichier_valide,
    extraire_infos_nom_fichier,
)

__all__ = [
    # fichiers_compilation
    "lister_fichiers_excel",
    "lire_fichiers_excel",
    "charger_fichiers_excel",
    "exporter_dataframe_excel",
    # fichiers_nommage
    "generer_nom_fichier",
    "generer_nom_feuille",
    "est_nom_fichier_valide",
    "extraire_infos_nom_fichier",
]
