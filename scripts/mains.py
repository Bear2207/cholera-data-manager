"""Script principal d'orchestration du pipeline Cholera.
Exécute : chargement -> nettoyage -> dédoublonnage -> analyse -> export
"""
from pathlib import Path
import pandas as pd
from config import INPUT_DIR, OUTPUT_DIR, NOM_FEUILLE, MOTIF_FICHIER, DATETIME_COLS
from data_loading import charger_et_fusionner, creer_resume
from cleaning import full_clean_pipeline
from deduplication import identifier_doublons, supprimer_doublons
from completeness import verifier_completude_provinces
from analysis import resume_par_province, tcd_par_province_et_semaine
from utils import exporter_dataframe_excel, safe_display


def main(
    dossier_donnees: str = INPUT_DIR,
    motif: str = MOTIF_FICHIER,
    sheet_name: str = NOM_FEUILLE,
    annee_filtre: int | None = 2025,
    semaine_min: int = 1,
    semaine_max: int = 52
):
    print("--- Début pipeline Cholera ---")

    # 1) Résumé rapide des fichiers
    df_resume, df_details = creer_resume(dossier=dossier_donnees, nom_feuille=sheet_name, afficher=False)
    print("Resume fichiers:")
    safe_display(df_resume)

    # 2) Chargement/fusion
    df_raw = charger_et_fusionner(dossier_racine=dossier_donnees, motif_fichier=motif, sheet_name=sheet_name, colonne_source='Provenance')
    print("Données brutes chargées :", df_raw.shape)

    # 3) Nettoyage complet
    df_clean = full_clean_pipeline(df_raw)
    print("Après nettoyage :", df_clean.shape)

    # 4) Filtre année si demandé
    if annee_filtre is not None:
        df_clean = df_clean.loc[df_clean['Annee_epi'] == annee_filtre].copy()
        print(f"Filtré sur l'année: {annee_filtre} -> {df_clean.shape}")

    # 5) Déduplication
    criteres_doublons = ["Nom_complet","Province_notification","Zone_de_sante_notification","Aire_de_sante_notification","Sexe","Age","Unite_age","Profession"]
    nbr, df_doublons = identifier_doublons(df_clean, criteres_doublons)
    print("Doublons détectés :", nbr)
    df_sans_doublons = supprimer_doublons(df_clean, criteres_doublons, keep='first')
    print("Après suppression doublons :", df_sans_doublons.shape)

    # 6) Complétude par provinces (exemple)
    provinces_attendues = [
        "Equateur","Kasai Central","Kasai Oriental","Kinshasa","Kongo Central","Kwilu","Lomami","Maindombe",
        "Maniema","Mongala","Nord Kivu","Sud Kivu","Tanganyika","Tshopo","Tshuapa"
    ]
    df_comp, df_resume_comp = verifier_completude_provinces(df_sans_doublons, provinces_attendues)
    print("Résumé complétude :")
    safe_display(df_resume_comp)

    # 7) Analyse basique
    print("Analyse par province :")
    summary_prov = resume_par_province(df_sans_doublons)
    safe_display(summary_prov)

    # 8) Export du jeu filtré par semaines (ex. semaine_min->semaine_max)
    df_export = df_sans_doublons.loc[df_sans_doublons['Num_semaine_epi'].between(semaine_min, semaine_max)]
    nom_fichier = f"rdc_compilation_LL_Cholera_SE{semaine_min:02d}_SE{semaine_max:02d}"
    exporter_dataframe_excel(df_export, OUTPUT_DIR, nom_fichier, sheet_name=sheet_name)

    print("--- Fin pipeline Cholera ---")


if __name__ == '__main__':
    main()