#!/usr/bin/env python3
"""
Orchestrateur principal du pipeline Cholera
Exécute toutes les étapes dans l'ordre
"""

import sys
import os
from datetime import datetime

# Ajouter le répertoire parent au chemin Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from scripts.utils import logger
    from scripts.config import *
except ImportError:
    # Fallback pour les imports directs
    from utils import logger
    from config import *

def executer_pipeline_complet():
    """Exécute le pipeline complet de traitement"""
    logger("🚀 DÉMARRAGE DU PIPELINE CHOLERA", "success")
    logger(f"📁 Dossier source: {CONFIG['dossier_donnees']}")
    logger(f"🎯 Année cible: {CONFIG['annee_filtre']}")
    
    debut = datetime.now()
    
    try:
        # Étape 1: Compilation
        try:
            from scripts.compilation import main as compiler
        except ImportError:
            from compilation import main as compiler
        df_compile, chemin_compile = compiler()
        
        # Étape 2: Fusion  
        try:
            from scripts.fusion import main as fusionner
        except ImportError:
            from fusion import main as fusionner
        df_fusion, chemin_fusion = fusionner()
        
        # Étape 3: Nettoyage
        try:
            from scripts.nettoyage import main as nettoyer
        except ImportError:
            from nettoyage import main as nettoyer
        df_nettoye, chemin_nettoye = nettoyer()
        
        # Étape 4: Export
        try:
            from scripts.export import main as exporter
        except ImportError:
            from export import main as exporter
        df_final, chemins_export = exporter()
        
        # Calcul du temps d'exécution
        duree = datetime.now() - debut
        
        logger("🎉 PIPELINE TERMINÉ AVEC SUCCÈS!", "success")
        logger(f"⏱️  Durée totale: {duree}")
        logger(f"📈 Évolution: {len(df_compile)} → {len(df_fusion)} → {len(df_nettoye)} → {len(df_final)} lignes")
        
        return df_final, chemins_export
        
    except Exception as e:
        logger(f"💥 ERREUR CRITIQUE DANS LE PIPELINE: {e}", "error")
        sys.exit(1)

def executer_etape_specifique(etape):
    """Exécute une étape spécifique du pipeline"""
    etapes = {
        'compilation': 'compilation',
        'fusion': 'fusion', 
        'nettoyage': 'nettoyage',
        'export': 'export'
    }
    
    if etape not in etapes:
        logger(f"Étape inconnue: {etape}", "error")
        return
    
    try:
        module_name = f"scripts.{etapes[etape]}"
        module = __import__(module_name, fromlist=['main'])
    except ImportError:
        module_name = etapes[etape]
        module = __import__(module_name, fromlist=['main'])
    
    module.main()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Exécuter une étape spécifique
        etape = sys.argv[1]
        logger(f"Exécution de l'étape: {etape}")
        executer_etape_specifique(etape)
    else:
        # Exécuter le pipeline complet
        executer_pipeline_complet()