#!/usr/bin/env python3
"""
Script pour inspecter rapidement la structure des données
"""

import pandas as pd
from pathlib import Path
import json

def inspect_data():
    data_dir = Path("data")
    output_dir = Path("db/data")
    
    print("=== INSPECTION DES DONNÉES CHOLERA ===\n")
    
    # Lister les fichiers
    fichiers = list(data_dir.glob("*_LL_Cholera_*.xlsx"))
    print(f"Fichiers trouvés ({len(fichiers)}):")
    for f in fichiers:
        print(f"  - {f.name}")
    
    # Inspecter le premier fichier en détail
    if fichiers:
        first_file = fichiers[0]
        print(f"\n=== INSPECTION DÉTAILLÉE DE {first_file.name} ===")
        
        try:
            # Lire le fichier
            df = pd.read_excel(first_file, sheet_name=0)
            print(f"Dimensions: {len(df)} lignes × {len(df.columns)} colonnes")
            print(f"\nColonnes:")
            for i, col in enumerate(df.columns):
                print(f"  {i:2d}. {col}")
            
            print(f"\nExemple de données (3 premières lignes):")
            for i in range(min(3, len(df))):
                print(f"  Ligne {i}:")
                for col in df.columns[:5]:  # Premières 5 colonnes seulement
                    val = df.iloc[i][col]
                    if pd.notna(val):
                        print(f"    {col}: {val}")
            
            # Statistiques basiques
            print(f"\nStatistiques par colonne:")
            for col in df.columns[:10]:  # 10 premières colonnes
                non_null = df[col].notna().sum()
                pct = (non_null / len(df)) * 100
                sample_vals = df[col].dropna().unique()[:3]
                print(f"  {col}: {non_null}/{len(df)} ({pct:.1f}%) - Ex: {sample_vals}")
                
        except Exception as e:
            print(f"Erreur: {e}")

if __name__ == "__main__":
    inspect_data()#!/usr/bin/env python3
"""
Script pour inspecter rapidement la structure des données
"""

import pandas as pd
from pathlib import Path
import json

def inspect_data():
    data_dir = Path("data")
    output_dir = Path("db/data")
    
    print("=== INSPECTION DES DONNÉES CHOLERA ===\n")
    
    # Lister les fichiers
    fichiers = list(data_dir.glob("*_LL_Cholera_*.xlsx"))
    print(f"Fichiers trouvés ({len(fichiers)}):")
    for f in fichiers:
        print(f"  - {f.name}")
    
    # Inspecter le premier fichier en détail
    if fichiers:
        first_file = fichiers[0]
        print(f"\n=== INSPECTION DÉTAILLÉE DE {first_file.name} ===")
        
        try:
            # Lire le fichier
            df = pd.read_excel(first_file, sheet_name=0)
            print(f"Dimensions: {len(df)} lignes × {len(df.columns)} colonnes")
            print(f"\nColonnes:")
            for i, col in enumerate(df.columns):
                print(f"  {i:2d}. {col}")
            
            print(f"\nExemple de données (3 premières lignes):")
            for i in range(min(3, len(df))):
                print(f"  Ligne {i}:")
                for col in df.columns[:5]:  # Premières 5 colonnes seulement
                    val = df.iloc[i][col]
                    if pd.notna(val):
                        print(f"    {col}: {val}")
            
            # Statistiques basiques
            print(f"\nStatistiques par colonne:")
            for col in df.columns[:10]:  # 10 premières colonnes
                non_null = df[col].notna().sum()
                pct = (non_null / len(df)) * 100
                sample_vals = df[col].dropna().unique()[:3]
                print(f"  {col}: {non_null}/{len(df)} ({pct:.1f}%) - Ex: {sample_vals}")
                
        except Exception as e:
            print(f"Erreur: {e}")

if __name__ == "__main__":
    inspect_data()