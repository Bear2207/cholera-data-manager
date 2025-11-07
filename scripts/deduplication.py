"""Gestion et déduplication des enregistrements.
"""
import pandas as pd
from dataminsante.analyse import gerer_doublons_avance, compter_par_plusieurs_categories


def identifier_doublons(df: pd.DataFrame, critere: list, afficher: bool = True):
    nbr = gerer_doublons_avance(df, critere, mode='compter_lignes', tri_ascendant=True, reset_index=True)
    df_doublons = gerer_doublons_avance(df, colonnes_inclues=critere, mode='afficher', tri_ascendant=True, marquer=True)
    if afficher:
        print(f"Nombre de doublons : {nbr}")
    return nbr, df_doublons


def supprimer_doublons(df: pd.DataFrame, critere: list, keep: str = 'first') -> pd.DataFrame:
    df_clean = gerer_doublons_avance(df, colonnes_inclues=critere, mode='nettoyer', tri_ascendant=True, reset_index=True, keep=keep)
    return df_clean