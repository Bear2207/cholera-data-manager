"""Utilitaires génériques pour le pipeline.
Contient quelques wrappers légers autour de pandas/dateminainte si besoin.
"""
from typing import List
import pandas as pd
from pathlib import Path
from config import OUTPUT_DIR


def safe_display(df: pd.DataFrame, n: int = 5):
    """Affiche les premières lignes d'un DataFrame (wrapper)."""
    print(df.head(n))


def exporter_dataframe_excel(df: pd.DataFrame, dossier: str | Path, base_nom: str, sheet_name: str = "Sheet1") -> Path:
    """Exporte un DataFrame vers Excel et retourne le chemin du fichier."""
    out_dir = Path(dossier)
    out_dir.mkdir(parents=True, exist_ok=True)
    chemin = out_dir / f"{base_nom}.xlsx"
    df.to_excel(chemin, sheet_name=sheet_name, index=False)
    print(f"Export: {chemin}")
    return chemin