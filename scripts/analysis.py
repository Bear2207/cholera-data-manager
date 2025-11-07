"""Analyse descriptive et tableaux croisés.
"""
import pandas as pd
from dataminsante.analyse import compter_par_plusieurs_categories, tableau_croise_dynamique, get_target_columns


def resume_par_province(df: pd.DataFrame, colonnes: list = None):
    if colonnes is None:
        colonnes = ['Province_notification']
    return compter_par_plusieurs_categories(df, colonnes)


def tcd_par_province_et_semaine(df: pd.DataFrame, semaine: int):
    df_semaine = df.loc[df['Num_semaine_epi'] == semaine]
    tcd = tableau_croise_dynamique(
        df=df_semaine,
        lignes="Province_notification",
        colonnes="Num_semaine_epi",
        valeurs="Nom_complet",
        aggfunc="count",
        fill_value=0,
        margins=True,
        margins_name="Total"
    )
    return tcd


def filtrer_par_semaine_et_annee(df: pd.DataFrame, annee: int = None, num_semaine_col: str = 'Num_semaine_epi'):
    if annee is None:
        return df
    return df.loc[df['Annee_epi'] == annee]