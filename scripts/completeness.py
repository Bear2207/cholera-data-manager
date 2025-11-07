"""Vérification de la complétude par provinces ou autres segments.
"""
import pandas as pd
from dataminsante.colonne_valeur.valeurs_completude import comparer_listes, calculer_completude


def verifier_completude_provinces(df: pd.DataFrame, provinces_attendues: list):
    provinces_reelles = df["Province_notification"].dropna().unique()
    resultat_listes = comparer_listes(provinces_attendues, provinces_reelles)
    resultat_calcul = calculer_completude(provinces_attendues, provinces_reelles)

    df_comparaison = pd.DataFrame({
        "Provinces attendues": provinces_attendues,
        "Présentes": [p in provinces_reelles for p in provinces_attendues],
        "Manquantes": [p if p not in provinces_reelles else "" for p in provinces_attendues]
    })

    df_resume_completude = pd.DataFrame({
        "Total provinces attendues": [resultat_calcul["nb_attendus"]],
        "Provinces trouvées": [resultat_calcul["nb_reçus"]],
        "Complétude (%)": [resultat_calcul["completude_%"]],
        "Provinces manquantes": [", ".join(resultat_calcul["manquantes"])]
    })

    return df_comparaison, df_resume_completude