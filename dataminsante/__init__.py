# -*- coding: utf-8 -*-
"""
Package : dataminsante
======================
Bibliothèque modulaire de gestion, compilation et analyse des données épidémiologiques
(Choléra, Rougeole, etc.).  

Sous-modules principaux :
- compilation       → chargement et fusion des fichiers Excel
- colonne_valeur    → nettoyage et standardisation des colonnes
- analyse           → analyses descriptives et statistiques
- visualisation     → graphiques (Plotly, Matplotlib)
- database          → structures de référence (provinces, codes, pyramide)
- liste_lineaire    → pipelines SOP / Liste Linéaire automatisés
"""

import logging

logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

logger.info("✅ Package 'dataminsante' initialisé avec succès.")
