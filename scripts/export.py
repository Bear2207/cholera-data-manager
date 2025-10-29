#!/usr/bin/env python3
"""
Étape 4: Export des données finales
"""

import pandas as pd
from datetime import datetime
from scripts.config import *
from scripts.utils import *

def exporter_donnees_finales(df):
    """Exporte les données vers différents formats"""
    logger("=== ÉTAPE 4: EXPORT DES DONNÉES ===")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    
    # Exporter vers Excel (rapport détaillé)
    nom_fichier_excel = f"rdc_compilation_LL_Cholera_{timestamp}.xlsx"
    chemin_excel = DATA_OUTPUTS_DIR / nom_fichier_excel
    
    try:
        with pd.ExcelWriter(chemin_excel, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='LL_Cholera', index=False)
            
            # Ajouter un onglet avec les statistiques
            stats = generer_statistiques_detaillees(df)
            stats.to_excel(writer, sheet_name='Statistiques', index=False)
            
        logger(f"Excel exporté: {chemin_excel}")
    except Exception as e:
        logger(f"Erreur export Excel: {e}", "error")
    
    # Exporter vers CSV (pour la base de données)
    nom_fichier_csv = "cholera_data_compiled.csv"
    chemin_csv = DB_DATA_DIR / nom_fichier_csv
    
    try:
        df.to_csv(chemin_csv, index=False, encoding='utf-8')
        logger(f"CSV exporté: {chemin_csv}")
    except Exception as e:
        logger(f"Erreur export CSV: {e}", "error")
    
    # Exporter vers Parquet (pour l'analyse)
    nom_fichier_parquet = f"cholera_data_compiled_{timestamp}.parquet"
    chemin_parquet = DATA_OUTPUTS_DIR / nom_fichier_parquet
    
    try:
        df.to_parquet(chemin_parquet, index=False)
        logger(f"Parquet exporté: {chemin_parquet}")
    except Exception as e:
        logger(f"Erreur export Parquet: {e}", "error")
    
    return chemin_excel, chemin_csv, chemin_parquet

def generer_statistiques_detaillees(df):
    """Génère des statistiques détaillées pour le rapport"""
    logger("Génération des statistiques détaillées...")
    
    stats = []
    
    # Statistiques générales
    stats.append({"Metric": "Total des cas", "Valeur": len(df)})
    stats.append({"Metric": "Colonnes", "Valeur": len(df.columns)})
    stats.append({"Metric": "Valeurs manquantes totales", "Valeur": df.isna().sum().sum()})
    
    # Période couverte
    if 'date_admission' in df.columns:
        dates_valides = df['date_admission'].notna()
        if dates_valides.any():
            stats.append({"Metric": "Date début", "Valeur": df[dates_valides]['date_admission'].min()})
            stats.append({"Metric": "Date fin", "Valeur": df[dates_valides]['date_admission'].max()})
    
    # Répartition par sexe
    if 'sexe' in df.columns:
        rep_sexe = df['sexe'].value_counts()
        for sexe, count in rep_sexe.items():
            stats.append({"Metric": f"Sexe - {sexe}", "Valeur": count})
    
    # Classification des cas
    if 'classification_finale' in df.columns:
        rep_class = df['classification_finale'].value_counts()
        for classe, count in rep_class.items():
            stats.append({"Metric": f"Classification - {classe}", "Valeur": count})
    
    # Provinces
    if 'province_notification' in df.columns:
        stats.append({"Metric": "Provinces distinctes", "Valeur": df['province_notification'].nunique()})
    
    return pd.DataFrame(stats)

def generer_rapport_final(df, chemins_export):
    """Génère un rapport final complet"""
    print("\n" + "="*70)
    print("RAPPORT FINAL - PIPELINE CHOLERA")
    print("="*70)
    print(f"📍 Données traitées: {len(df):,} cas")
    print(f"📊 Colonnes finales: {len(df.columns)}")
    print(f"📅 Période: {CONFIG['semaine_epi_min']} à {CONFIG['semaine_epi_max']} ({CONFIG['annee_filtre']})")
    
    if 'classification_finale' in df.columns:
        print(f"🔬 Classification:")
        for classe, count in df['classification_finale'].value_counts().items():
            print(f"   - {classe}: {count:,}")
    
    print(f"\n📁 Fichiers générés:")
    for format, chemin in zip(['Excel', 'CSV', 'Parquet'], chemins_export):
        print(f"   - {format}: {chemin}")
    
    print("="*70)

def executer_export():
    """Exécute l'étape d'export"""
    # Charger les données nettoyées
    df_nettoye = charger_etape_precedente(CLEANED_DIR, "03_donnees_nettoyees", 'parquet')
    
    # Exporter vers différents formats
    chemins_export = exporter_donnees_finales(df_nettoye)
    
    # Générer le rapport final
    generer_rapport_final(df_nettoye, chemins_export)
    
    return df_nettoye, chemins_export

def main():
    """Fonction principale d'export"""
    try:
        df_final, chemins = executer_export()
        logger("Export terminé avec succès!", "success")
        return df_final, chemins
    except Exception as e:
        logger(f"Erreur lors de l'export: {e}", "error")
        raise

if __name__ == "__main__":
    main()