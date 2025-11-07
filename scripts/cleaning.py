"""Nettoyage et normalisation des données choléra.
Toutes les fonctions s'appuient sur `dataminsante` pour garder le même comportement.
"""
from typing import List
import pandas as pd
from dataminsante.colonne_valeur import *
from dataminsante.colonne_valeur.valeurs_completude import *
from dataminsante.database import *
from dataminsante.liste_lineaire import *
from dataminsante.liste_lineaire.sop_pipeline import *
from dataminsante.analyse import *
from dataminsante.visualisation import *
from config import COLONNES_CHOLERA, DATETIME_COLS


def prepare_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Supprime les colonnes inutiles, ajoute les colonnes manquantes et réordonne.
    Utilise les helpers dataminsante présents dans ton script initial.
    """
    df = supprimer_colonnes_inutiles(df, colonnes_a_garder=COLONNES_CHOLERA)
    df = ajouter_colonnes_manquantes(df, colonnes=COLONNES_CHOLERA)
    df = reclasser_colonnes(df, colonnes_prioritaires=COLONNES_CHOLERA)
    return df


def fusionner_colonnes_similaires(df: pd.DataFrame) -> pd.DataFrame:
    """Fusionne colonnes similaires (automatique + manuel)."""
    df = clean_all_column_names(df.copy())
    df = fusionner_colonnes_similaires_ou_groupes(
        df,
        method="similarity",
        type_fusion="first_non_null",
        seuil_similarite=1,
        drop=True
    )
    # Fusions manuelles spécifiques
    colonnes_a_fusionner = {
        "Zone_de_sante_notification": ['Zone_de_sante','Zone_de_sante_notification'],
        "N_epid": ['N_epid', 'Id'],
        "Traitement_antibiotique" : ['Traitement_antibiotique','Traitement'],
        "Province_notification": ['Province_notification','Province'],
        "Zone_de_sante_notification" : ['Zone_de_sante_notification', 'Zone_de_sante']
    }
    df = fusionner_colonnes_similaires_ou_groupes(
        df,
        method="manual",
        groupes_colonnes=colonnes_a_fusionner,
        type_fusion="first_non_null",
        drop=True
    )
    return df


def convert_and_filter_dates(df: pd.DataFrame, colonnes_datetime: List[str] = DATETIME_COLS, annee_min: int | None = None) -> pd.DataFrame:
    """Convertit colonnes en datetime et filtre sur l'année si fournie.
    Remarque: ton script initial appelait `filtrer_par_premiere_date` après conversion.
    """
    df = convert_column_to_date(df, colonnes_datetime)
    if annee_min is not None:
        df = filtrer_par_premiere_date(df, colonnes_datetime, annee_min)
    return df


def nettoyer_demographiques_ages(df: pd.DataFrame) -> pd.DataFrame:
    """Nettoyage des champs démographiques et calcul des tranches d'age.
    Reprend la logique de ton script: extraction des nombres, fusion age_annee/age_mois, creation des tranches.
    """
    # Nom complet
    df = clean_all_values(df, cols='Nom_complet', case_option="upper", remove_accents=True, convert_type=False, verbose=False)

    # Age_annee
    df['Age_annee'] = df['Age_annee'].apply(lambda x: extraire_texte_et_nombre(x, valeur_par_defaut="ans", detecter_annee=True, normaliser_texte=True, mode="nombre")).astype(float)
    df['Age_mois'] = df['Age_mois'].apply(lambda x: extraire_texte_et_nombre(x, valeur_par_defaut="mois", detecter_annee=True, normaliser_texte=True, mode="nombre")).astype(float)

    # Fusion age années / mois
    df = fusionner_colonnes_Age_annee_Age_mois(
        df,
        col_age_annee="Age_annee",
        col_age_mois="Age_mois",
        nom_colonne_age="Age",
        nom_colonne_unite="Unite_age",
        age_limite_en_annees=5.0,
        arrondi_mois=1,
        arrondi_annees=2,
        drop_originals=False
    )

    # Tranches
    df = creer_tranche_age_avec_unite_generique(df,'Age','Unite_age')
    df = creer_tranche_age_avec_unite(df, col_age='Age', col_unite='Unite_age', mode='5ans', col_tranche='Tranche_age_en_ans')
    return df


def nettoyer_geographie(df: pd.DataFrame) -> pd.DataFrame:
    """Remplit Province/Zone/Aire à partir des références et normalise les valeurs.
    Utilise la database pyramide (fichier Excel dans data/).
    """
    # Compléter Province à partir de Provenance
    df["Province_notification"] = df["Provenance"].apply(lambda x: trouver_province(x, code_provinces_deux_lettres))

    # Remplissage via dictionnaire pyramide
    dictionnaires = creer_dictionnaires_pyramide(df_ref=clean_database_pyramide())
    df = remplir_colonne_depuis_reference(
        df=df,
        colonne_a_remplir="Zone_de_sante_notification",
        colonne_reference=["N_epid_prov","N_epid"],
        type_reference="N_epid",
        dictionnaires=dictionnaires,
        variable_remplissage="Zone_de_sante"
    )

    # Nettoyer valeurs via df_ref
    df_ref = pd.read_excel("data/rdc_database_pyramide_code.xlsx")
    colonnes_a_nettoyer_dans_df_dirty = ["Zone_de_sante_notification", "Aire_de_sante_notification"]
    mapping_colonnes_df_clean_df_ref = {
        "Province_notification": "Province",
        "Province_provenance":"Province",
        "Zone_de_sante_notification": "Zone_de_sante",
        "Zone_de_sante_provenance":"Zone_de_sante",
        "Aire_de_sante_notification": "Aire_de_sante",
        "Aire_de_sante_provenance": "Aire_de_sante"
    }
    df = nettoyer_colonnes(
        df,
        df_ref,
        col_dirty_boucle="Province_notification",
        cols_a_nettoyer=colonnes_a_nettoyer_dans_df_dirty,
        mapping_colonnes=mapping_colonnes_df_clean_df_ref,
        seuil=85
    )

    # Normaliser noms (première lettre de chaque mot en majuscule)
    premiere_lettre_chaque_mot_Maj=[
        'Province_notification','Zone_de_sante_notification','Aire_de_sante_notification',
        'Province_provenance','Zone_de_sante_provenance','Aire_de_sante_provenance',
    ]
    df = normaliser_values(df, premiere_lettre_chaque_mot_Maj, case_option='title', remove_accents=True)
    return df


def normaliser_autres_valeurs(df: pd.DataFrame) -> pd.DataFrame:
    """Normalisation fine des colonnes texte et valeurs catégorielles."""
    premiere_lettre_Maj=[
        'Profession','Prise_antibiotique_avant_admission','Antecedents_morbides','Femme_enceinte',
        'Hospitalisation','Prelevement','TDR_realise','Traitement_antibiotique','Degre_deshydratation',
        'Source_approvisionnement_en_eau','TDR_Resultat','TDR_Archive','Issue','Observation','Resultat_labo_pcr','Statut_vaccinal'
    ]
    colonnes_oui_non = ['Prise_antibiotique_avant_admission','Antecedents_morbides','Femme_enceinte','Hospitalisation','Prelevement','TDR_realise','Traitement_antibiotique']
    df = clean_all_values(df, premiere_lettre_Maj + colonnes_oui_non, case_option='capitalize', remove_accents=True)
    return df


def remplacer_valeurs_critere(df: pd.DataFrame) -> pd.DataFrame:
    """Remplace valeurs spécifiques selon le fichier "data/Replace_values.xlsx" (comme dans ton script)."""
    critere = {
        "Sexe": "Sexe",
        "TDR_realise": "TDR_realise",
        "TDR_Resultat": "TDR_Resultat",
        "Resultat_labo": "Resultat_labo",
        "Resultat_labo_pcr":"Resultat_labo_pcr",
        "Prelevement": "Prelevement",
        "Hospitalisation": "Hospitalisation",
        "Degre_deshydratation" : "Degre_deshydratation",
        "Prise_antibiotique_avant_admission" : "Prise_antibiotique_avant_admission",
        "Resultat_labo_culture": "Resultat_labo_culture",
        "Issue": "Issue"
    }
    critere_cols = list(critere.keys())
    df = replace_specific_values_critere(
        df=df,
        critere=critere,
        mapping_file="data/Replace_values.xlsx",
        regex_mode=True,
        clean_before=True,
        strip_lower=True
    )
    afficher_valeurs_uniques(df, colonnes=critere_cols)
    return df


def full_clean_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    """Exécute l'ensemble du nettoyage sur un DataFrame brut.
    Retourne le DataFrame nettoyé.
    """
    df = prepare_columns(df)
    df = fusionner_colonnes_similaires(df)
    df = convert_and_filter_dates(df, DATETIME_COLS, annee_min=None)
    df = nettoyer_demographiques_ages(df)
    df = nettoyer_geographie(df)
    df = normaliser_autres_valeurs(df)
    df = remplacer_valeurs_critere(df)
    df = reclasser_colonnes(df, colonnes_prioritaires=COLONNES_CHOLERA)
    return df