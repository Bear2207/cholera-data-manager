#!/usr/bin/env python3
"""
Fonctions utilitaires communes pour le pipeline Cholera
"""

import pandas as pd
import numpy as np
import re
import os
from datetime import datetime
from pathlib import Path

def logger(message, type="info"):
    """Journalisation des messages"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prefix = {
        "info": "ℹ️",
        "success": "✅", 
        "warning": "⚠️",
        "error": "❌"
    }.get(type, "ℹ️")
    
    print(f"{timestamp} {prefix} {message}")

def nettoyer_nom_colonne(name):
    """Nettoie un nom de colonne"""
    if pd.isna(name):
        return "colonne_inconnue"
    name = str(name).strip()
    name = re.sub(r'[^\w\s]', '_', name)
    name = re.sub(r'\s+', '_', name)
    return name.lower()

def verifier_fichiers_excel(dossier_donnees, motif_fichier):
    """Vérifie la présence des fichiers Excel"""
    import glob
    
    pattern = dossier_donnees / motif_fichier
    fichiers = glob.glob(str(pattern))
    
    if not fichiers:
        raise FileNotFoundError(f"Aucun fichier trouvé avec le pattern: {pattern}")
    
    logger(f"Fichiers trouvés ({len(fichiers)}):")
    for f in fichiers:
        logger(f"  - {os.path.basename(f)}")
    
    return fichiers

def sauvegarder_etape(df, dossier, nom_fichier, format='csv'):
    """Sauvegarde le dataframe à une étape du processus"""
    dossier.mkdir(parents=True, exist_ok=True)
    
    if format == 'csv':
        chemin = dossier / f"{nom_fichier}.csv"
        df.to_csv(chemin, index=False, encoding='utf-8')
    elif format == 'excel':
        chemin = dossier / f"{nom_fichier}.xlsx"
        df.to_excel(chemin, index=False)
    elif format == 'parquet':
        chemin = dossier / f"{nom_fichier}.parquet"
        df.to_parquet(chemin, index=False)
    
    logger(f"Données sauvegardées: {chemin}")
    return chemin

def charger_etape_precedente(dossier, nom_fichier, format='csv'):
    """Charge les données d'une étape précédente"""
    if format == 'csv':
        chemin = dossier / f"{nom_fichier}.csv"
        df = pd.read_csv(chemin, encoding='utf-8')
    elif format == 'excel':
        chemin = dossier / f"{nom_fichier}.xlsx"
        df = pd.read_excel(chemin)
    elif format == 'parquet':
        chemin = dossier / f"{nom_fichier}.parquet"
        df = pd.read_parquet(chemin)
    
    logger(f"Données chargées: {chemin}")
    return df

def generer_rapport_etape(df, nom_etape):
    """Génère un rapport pour une étape"""
    print(f"\n" + "="*60)
    print(f"RAPPORT - {nom_etape.upper()}")
    print("="*60)
    print(f"Lignes: {len(df):,}")
    print(f"Colonnes: {len(df.columns)}")
    print(f"Valeurs manquantes: {df.isna().sum().sum():,}")
    
    if 'date_admission' in df.columns:
        dates_valides = df['date_admission'].notna()
        if dates_valides.any():
            print(f"Période: {df[dates_valides]['date_admission'].min()} à {df[dates_valides]['date_admission'].max()}")
    
    print("="*60)