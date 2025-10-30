#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import numpy as np
import os
from datetime import datetime
import re
from unidecode import unidecode

# Import des fonctions de dataminsante
from dataminsante.compilation import *
from dataminsante.colonne_valeur import *
from dataminsante.analyse import *
from dataminsante.visualisation import *
from dataminsante.database import *
from dataminsante.liste_lineaire import *
from dataminsante.liste_lineaire.sop_pipeline import *

def setup_logging():
    """Configuration du logging"""
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('cholera_pipeline.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def get_current_epi_week():
    """Obtenir la semaine épidémiologique actuelle"""
    today = datetime.now()
    return today.isocalendar()[1]

def validate_dataframe(df, operation_name):
    """Valider l'intégrité d'un DataFrame"""
    logger = setup_logging()
    if df is None:
        logger.error(f"DataFrame est None pour l'opération: {operation_name}")
        return False
    
    if df.empty:
        logger.warning(f"DataFrame vide pour l'opération: {operation_name}")
        return False
    
    logger.info(f"DataFrame validé pour {operation_name}: {len(df)} lignes, {len(df.columns)} colonnes")
    return True