#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# -- Fichiers de compilation --
from dataminsante.compilation import *
# -- Nettoyage des données --
from dataminsante.colonne_valeur import *
# -- Statistiques descriptives --
from dataminsante.analyse import *
# -- Visualisation --
from dataminsante.visualisation import *
# pyramide
from dataminsante.database import *
# Verification renommage
from dataminsante.liste_lineaire import *
# Verification renommage
from dataminsante.liste_lineaire.sop_pipeline import *


# PRE-TEST

# In[ ]:


# Chemin du dossier contenant les fichiers Excel
dossier_donnees = r"C:\Users\Benjamin MUPANZI\Documents\dataminsante\Cholera\SE41"
motif_fichier = "*_LL_Cholera_*.xlsx"
nom_feuille = "LL_Cholera"


# In[ ]:


resume = verifier_excel_recursive(dossier_donnees, nomenclature="resume",mode="tous", nom_feuille=nom_feuille, afficher=False,detecter_header=True)
df_resume, df_details = creer_df_resume(resume)
display(df_resume,df_details)


# SOP

# In[ ]:


# # SOP 
# resultats = pipeline_sop(
#     dossier_racine=dossier_donnees,
#     motif_fichier=motif_fichier,
#     sheet_name=nom_feuille,
#     colonne_source="Provenance",
#     dossier_sortie="output/",
#     nomenclature="resume" ,
#     mode="tous"
# )

# df_fusionne = resultats.get("df_fusionne")
# df_log = resultats.get("df_log")
# df_resume = resultats.get("df_resume")


# COMPILATION

# In[ ]:


# Fusion et nettoyage
df_compilation = charger_fichiers_excel(
    dossier_racine=dossier_donnees,
    motif_fichier=motif_fichier,
    sheet_name=nom_feuille,
    colonne_source="Provenance"
)
# Afficher les 5 premières lignes du DataFrame fusionné
df_compilation.head()


# In[ ]:


# # Fusion et nettoyage avec log
# df_compilation, df_log = charger_fichiers_excel_avec_log(
#     dossier_racine=dossier_donnees,
#     motif_fichier=motif_fichier,
#     sheet_name=nom_feuille,
#     colonne_source="Provenance"
# )

# display(df_compilation.head(),df_log.head())


# In[ ]:


colonne_cholera= [
'Provenance', # Dérivée
'N',
'N_epid_prov',
'N_epid',
'Statut_a_l_arrivee',
'Date_arrivee_malade',
'Date_admission',
'Date_notification',
'Date_investigation',
'Date_debut_maladie',
'Province_notification',
'Zone_de_sante_notification',
'Aire_de_sante_notification',
'Semaine_epid',
'Num_semaine_epi', # dérivées
'Annee_epi', # dérivées
'Nom_complet',
'Sexe',
'Age_annee',
'Age_mois',
'Age', # dérivées
'Unite_age', # dérivées
'Age_en_ans',
'Tranche_age', # dérivées
'Tranche_age_en_ans', # dérivées
'Profession',
'Province_provenance',
'Zone_de_sante_provenance',
'Aire_de_sante_provenance',
'Adresse',
'Symptomes',
'Prise_antibiotique_avant_admission',
'Nom_antibiotique',
'Antecedents_morbides',
'Femme_enceinte',
'Degre_deshydratation',
'Plan_de_deshydratation',
'Hospitalisation',
'Prelevement',
'Date_prelevement',
'TDR_realise',
'TDR_Resultat',
'TDR_archive',
'Resultat_labo',
'Resultat_labo_culture',
'Serotype',
'Nom_structure_realisant_le_tdr',
'Resultat_labo_pcr',
'Traitement_antibiotique',
'Quantite_total_ringer_recue',
'Quantite_total_sro_recue',
'Ctc_utc',
'Issue',
'Date_de_sortie_malade',
'Etat_sortie_malade',
'Statut_vaccinal',
'Nombre_dose',
'Annee_vaccination',
'Source_eventuelle_de_contamination',
'Source_approvisionnement_en_eau',
'Classification_finale',
'Date_de_guerie',
'Observation'
]

# Supprimer les colonnes inutiles
df_compilation=supprimer_colonnes_inutiles(df_compilation,colonnes_a_garder=colonne_cholera)
df_compilation=ajouter_colonnes_manquantes(df_compilation, colonnes=colonne_cholera)
df_compilation=reclasser_colonnes(df_compilation,colonnes_prioritaires=colonne_cholera)
df_compilation.head()


# FUSION

# In[ ]:


df_fusion=clean_all_column_names(df_compilation.copy())
df_fusion


# In[ ]:


# Fusion des colonnes identiques
df_fusion= fusionner_colonnes_similaires_ou_groupes(
    df_fusion,
    method="similarity",
    type_fusion="first_non_null",
    seuil_similarite=1,
    drop=True
)
df_fusion.head()


# In[ ]:


# Fusion des colonnes identiques
colonnes_a_fusionner = {
    # Zone de notification
    "Zone_de_sante_notification": ['Zone_de_sante','Zone_de_sante_notification'],
    "N_epid": ['N_epid', 'Id'],
    "Traitement_antibiotique" : ['Traitement_antibiotique','Traitement'],
    "Province_notification": ['Province_notification','Province'],
    "Zone_de_sante_notification" : ['Zone_de_sante_notification', 'Zone_de_sante']

}
df_fusion = fusionner_colonnes_similaires_ou_groupes(
    df_fusion,
    method="manual",
    groupes_colonnes=colonnes_a_fusionner,
    type_fusion="first_non_null",
    drop=True
)
df_fusion.head()


# In[ ]:


# Conversion en datetime
colonnes_datetime=['Date_arrivee_malade','Date_admission', 'Date_debut_maladie','Date_prelevement','Date_de_sortie_malade']
df_fusion=convert_column_to_date(df_fusion,colonnes_datetime)
# Filter par année : 2025
df_fusion=filtrer_par_premiere_date(df_fusion,colonnes_datetime, 2025)


# NETTOYAGE
# 

# In[ ]:


df_clean=df_fusion.copy()
df_clean.head()


# In[ ]:


# Colonnes epi
colonne_epi=['N_epid','N_epid_prov','Semaine_epid','Provenance']
# Colonnes datetime
colonnes_datetime=['Date_arrivee_malade','Date_admission', 'Date_debut_maladie','Date_prelevement','Date_de_sortie_malade']
# Colonnes humaines
colonnes_nom_patient = ['Nom_complet','Sexe','Age','Unite_age','Profession','Adresse']
# colonnes database_pyramide
colonnes_database_pyramide = ['Province_notification','Zone_de_sante_notification','Aire_de_sante_notification',
                              'Province_provenance', 'Zone_de_sante_provenance','Aire_de_sante_provenance']
# Colonnes numériques
colonnes_numeriques = ['Quantite_total_ringer_recue','Quantite_total_sro_recue','Nombre_dose']
# Colonnes booléennes
colonnes_oui_non = ['Prise_antibiotique_avant_admission','Antecedents_morbides','Femme_enceinte','Hospitalisation','Prelevement','TDR_realise','Traitement_antibiotique']
# Resulata
colonne_resulat=['TDR_realise','TDR_Resultat','Resultat_labo_pcr','Issue']
# Symptomes
colonnes_symptomes = ['Symptomes','Nom_antibiotique','Degre_deshydratation','Serotype','Source_eventuelle_de_contamination','Source_approvisionnement_en_eau']


# In[ ]:


colonnes_ordre_1 = (
	colonne_epi +
	colonnes_database_pyramide +
	colonnes_nom_patient +
	colonnes_datetime +
	colonnes_oui_non +
	colonnes_symptomes +
	colonne_resulat
)

df_clean=reclasser_colonnes(df_clean, colonnes_prioritaires=colonnes_ordre_1)
df_clean.head()


# - Colonnes

# -- Variables identifiants / uniques

# In[ ]:


# Nettoyage : colonnes
"""
N_epid
N_epid_prov
"""
df_clean = nettoyer_numero_epi(df_clean, ["N_epid","N_epid_prov"])
df_clean.head()


# -- Variables numérique

# In[ ]:


# Nettoyage : colonnes
"""
numerique
"""
# Conversion en Numerique
df_clean=convertir_en_int(df_clean,colonnes_numeriques)


# -- Variables temporelles

# In[ ]:


# Nettoyage : colonnes
"""
datetime
"""
# Conversion en datetime
df_clean=convert_column_to_date(df_clean,colonnes_datetime)


# In[ ]:


# Nettoyage : colonnes
"""
Semaine_epid
Annee_epi
"""
# Semaine_epi
df_clean=ajouter_annee_semaine_epi(df_clean,colonnes_datetime,'Semaine_epid',separer_colonnes=True,remplacer_si_existe=True,ordre="semaine-annee")
# Anne_epi
df_clean["Annee_epi"]=df_clean["Annee_epi"].replace({2035: 2025})


# -- Variables démographiques

# In[ ]:


# Nettoyage : colonnes
"""
Nom complet incluant le nom et le prénom

"""
df_clean=clean_all_values(df_clean, cols='Nom_complet', case_option="upper", remove_accents=True,convert_type=False,verbose=False)


# In[ ]:


# Nettoyage : colonnes
"""
Age
Unite_age 
"""

# Uniformiser les âges en annees
df_clean['Age_annee'] = df_clean['Age_annee'].apply(
    lambda x: extraire_texte_et_nombre(
        x,
        valeur_par_defaut="ans",
        detecter_annee=True,
        normaliser_texte=True,
        mode="nombre"
    )
).astype(float)

# Remplacer les valeurs > 120 (âge max plausible) par NaN
# df_clean.loc[df_clean['Age_mois'] > 120, 'Age_mois'] = float('nan')

# Uniformiser les âges en mois
df_clean['Age_mois'] = df_clean['Age_mois'].apply(
    lambda x: extraire_texte_et_nombre(
        x,
        valeur_par_defaut="mois",
        detecter_annee=True,
        normaliser_texte=True,
        mode="nombre"
    )
).astype(float)

# Remplacer les valeurs > 120 (âge max plausible) par NaN
# df_clean.loc[df_clean['Age_mois'] > 120, 'Age_mois'] = float('nan')

# Fusionner les colonnes Age_annee et Age_mois
df_clean = fusionner_colonnes_Age_annee_Age_mois(
    df_clean, 
    col_age_annee="Age_annee", 
    col_age_mois="Age_mois", 
    nom_colonne_age="Age", 
    nom_colonne_unite="Unite_age", 
    age_limite_en_annees=5.0, 
    arrondi_mois=1, 
    arrondi_annees=2, 
    drop_originals=False
)


# In[ ]:


# Nettoyage : colonnes
"""
Tranche_age
"""
# Tranche Age
df_clean=creer_tranche_age_avec_unite_generique(df_clean,'Age','Unite_age')

# Créer la colonne 'Tranche_age_en_ans'
df_clean=creer_tranche_age_avec_unite(
    df_clean,
    col_age='Age',
    col_unite='Unite_age',
    mode='5ans',
    col_tranche='Tranche_age_en_ans'
)
df_clean.head()


# -- Variables géographiques

# In[ ]:


# Nettoyage : colonnes
"""
Provinces
"""
# Completer des provinces : SNIS
df_clean["Province_notification"] = df_clean["Provenance"].apply(lambda x: trouver_province(x, code_provinces_deux_lettres))
# df_clean["Province_notification"] = df_clean["Provenance"].apply(lambda x: trouver_province_standard(x, code_provinces_deux_lettres, "", "_"))

# Completer des provinces : OMS
# df_fusion["Province_notification"] = df_fusion["Provenance"].apply(lambda x: trouver_province_standard(x, code_provinces_trois_lettres, "DPS_", "_"))


# In[ ]:


# Remplissage : colonnes
"""
Zones de santé
"""
dictionnaires = creer_dictionnaires_pyramide(df_ref=clean_database_pyramide())

# Remplir les zones à partir de N_epid
df_clean = remplir_colonne_depuis_reference(
    df=df_clean,
    colonne_a_remplir="Zone_de_sante_notification",
    colonne_reference=["N_epid_prov","N_epid"],
    type_reference="N_epid",
    dictionnaires=dictionnaires,
    variable_remplissage="Zone_de_sante"
)
df_clean.head()


# In[ ]:


# Remplissage et nettoyage : colonnes
"""
Zones de santé
Aire de santé
"""

# Remplir en se référant à la pyramide
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
df_clean = nettoyer_colonnes(
    df_clean, 
    df_ref,
    col_dirty_boucle="Province_notification",
    cols_a_nettoyer=colonnes_a_nettoyer_dans_df_dirty,
    mapping_colonnes=mapping_colonnes_df_clean_df_ref,
    seuil=85
)
df_clean=reclasser_colonnes(df_clean,colonnes_prioritaires=colonne_cholera)
df_clean.head()


# In[ ]:


# Normalisation : colonnes
"""

"""

# Colonnes première de chaque mot en Majuscule
premiere_lettre_chaque_mot_Maj=[
    'Province_notification',
    'Zone_de_sante_notification',
    'Aire_de_sante_notification',
    'Province_provenance',
    'Zone_de_sante_provenance',
    'Aire_de_sante_provenance',
    ]
df_clean=normaliser_values(df_clean,premiere_lettre_chaque_mot_Maj ,case_option='title',remove_accents=True)


# -- Variables Autres

# In[ ]:


# Nettoyage : colonnes
"""
Colonnes première lettre en majuscule
"""
# Colonnes première lettre en majuscule
premiere_lettre_Maj=[
    'Profession',
    'Prise_antibiotique_avant_admission',
    'Antecedents_morbides',
    'Femme_enceinte',
    'Hospitalisation',
    'Prelevement',
    'TDR_realise',
    'Traitement_antibiotique',
    'Degre_deshydratation',
    'Source_approvisionnement_en_eau',
    'TDR_Resultat',
    'TDR_Archive',
    'Issue',
    'Observation',
    'Resultat_labo_pcr',
    'Statut_vaccinal'
    ]

df_clean=clean_all_values(df_clean,premiere_lettre_Maj + colonnes_oui_non ,case_option='capitalize',remove_accents=True)


# - Valeurs

# In[ ]:


# Nettoyage : valeurs de colonnes
"""
Resultat    
"""
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

critere_cols=list(critere.keys())

# Remplacer les valeurs spécifiques dans la colonne
df_clean = replace_specific_values_critere(
    df=df_clean,
    critere=critere,
    mapping_file="data/Replace_values.xlsx",
    regex_mode=True,
    clean_before=True,
    strip_lower=True
)

afficher_valeurs_uniques(df_clean, colonnes=critere_cols)


# - Compilation des compilés

# In[ ]:


# Fusion des fichiers compilés
dossier_donnees = "output"
motif_fichier = "rdc_compilation_LL_Cholera_*.xlsx"
nom_feuille = "LL_Cholera"
# Fusion et nettoyage
df_clean = charger_fichiers_excel(
    dossier_racine=dossier_donnees,
    motif_fichier=motif_fichier,
    sheet_name=nom_feuille,
    colonne_source=None
)

#  Nettoyage des colonnes
df_clean=clean_all_column_names(df_clean)
# Colonnes datetime
colonnes_datetime=['Date_arrivee_malade','Date_admission', 'Date_debut_maladie','Date_prelevement','Date_de_sortie_malade']
# Afficher les 5 premières lignes du DataFrame fusionné
df_clean.head()


# - Doublons

# In[ ]:


df_clean_2025 = df_clean[df_clean['Annee_epi'] == 2025].copy()
df_clean_2025.head()


# In[ ]:


critere_doublons=["Nom_complet","Province_notification","Zone_de_sante_notification","Aire_de_sante_notification","Sexe","Age","Unite_age","Profession"]
# Toutes les lignes en doublons
nbr_doublons=gerer_doublons_avance(
    df_clean_2025, 
    critere_doublons,
    mode='compter_lignes', 
    tri_ascendant=True, 
    reset_index=True
)
# Affichage complet des doublons
df_clean_2025_doubons=gerer_doublons_avance(
    df_clean_2025, 
    colonnes_inclues=critere_doublons,
    mode='afficher', 
    tri_ascendant=True, 
    marquer=True,
    # export_path="output/doublons_cholera_2025.xlsx"
)
display(f"Nombre de doublons : {nbr_doublons}")
display(df_clean_2025_doubons)


# In[ ]:


# Afficher les doublons où le nombre de cas > 2
result = compter_par_plusieurs_categories(df_clean_2025, critere_doublons)
resultat_2=result[result["Nombre de cas"] >= 2].sort_values(by="Province_notification", ascending=True)
# Afficher les doublons par province
compter_par_plusieurs_categories(resultat_2, "Province_notification")


# In[ ]:


# Suppression des doublons
df_sans_doublons=gerer_doublons_avance(
    df_clean_2025,
    colonnes_inclues=critere_doublons,
    mode='nettoyer',
    tri_ascendant=True,
    reset_index=True,
    keep='first' 
)
df_sans_doublons=reclasser_colonnes(df_sans_doublons, colonnes_prioritaires=colonne_cholera)
df_sans_doublons.head()


# In[ ]:


# Reprendre la Tranche Age
df_sans_doublons=creer_tranche_age_avec_unite_generique(df_sans_doublons,'Age','Unite_age')


# In[ ]:


# Critère de cas suspect et confirmé 
critere_suspect = {
    "TDR_Resultat": ["Positif","probable","inconnu"],
    "Symptomes":["DIARRHEE","DESHYDRATATION","DIARRHEES ET VOMISSENTS","SEULLES LIQUIDE ET VOMISSENT"]
}
critere_confirme = {
    "TDR_realise": "Positif"

}
classer_cas(
    df=df_sans_doublons,
    critere_suspect=critere_suspect,    
    critere_confirme=critere_confirme,
    regex_mode= True,
    nom_maladie= "Cholera"
)


# In[ ]:


# Nettoyage : colonnes
"""
Semaine_epid
Annee_epi
"""
# Semaine_epi
df_sans_doublons=ajouter_annee_semaine_epi(df_sans_doublons,colonnes_datetime,'Semaine_epid',separer_colonnes=True,remplacer_si_existe=True,ordre="semaine-annee")
# Anne_epi
df_sans_doublons["Annee_epi"]=df_sans_doublons["Annee_epi"].replace({2035: 2025})
df_sans_doublons


# In[10]:


# Forcer la conversion des colonnes d'âge en numérique
df_sans_doublons['Age_annee'] = pd.to_numeric(df_sans_doublons['Age_annee'], errors='coerce')
df_sans_doublons['Age_mois'] = pd.to_numeric(df_sans_doublons['Age_mois'], errors='coerce')

# Supprimer les autres colonnes inutiles
df_sans_doublons.loc[df_sans_doublons['Age_annee'] > 120, 'Age_annee'] = float('nan')  # Âge en années > 120
df_sans_doublons.loc[df_sans_doublons['Age_mois'] > 120, 'Age_mois'] = float('nan')    # Âge en mois > 120

# Normalisation des valeurs textuelles
df_sans_doublons = normaliser_values(
    df_sans_doublons,
    premiere_lettre_chaque_mot_Maj,
    case_option='title',
    remove_accents=True
)

df_sans_doublons=nettoyer_valeurs_vides(df_sans_doublons)

# Exporter
semaine_epi_min =1
semaine_epi_max = 41
nom_fichier = f"rdc_compilation_LL_Cholera_SE0{semaine_epi_min}_SE{semaine_epi_max}"
df_semaine_epi = df_sans_doublons.loc[df_sans_doublons['Num_semaine_epi'].between(semaine_epi_min, semaine_epi_max)]

chemin_export = exporter_dataframe_excel(
    df=df_semaine_epi,
    dossier="output",
    base_nom=nom_fichier,
    sheet_name="LL_Cholera"
)


# COMPLETUDE

# In[ ]:


from dataminsante.colonne_valeur.valeurs_completude import *

# Liste des provinces attendues
provinces_cholera = [
    "Equateur",
    "Kasai Central",
    "Kasai Oriental",
    "Kinshasa",
    "Kongo Central",
    "Kwilu",
    "Lomami",
    "Maindombe",
    "Maniema",
    "Mongala",
    "Nord Kivu",
    "Sud Kivu",
    "Tanganyika",
    "Tshopo",
    "Tshuapa"
]

# Provinces présentes dans les données
provinces_compile_cholera = df_sans_doublons["Province_notification"].unique()

# Comparaison normalisée
resultat_listes = comparer_listes(provinces_cholera, provinces_compile_cholera)
resultat_calcul = calculer_completude(provinces_cholera, provinces_compile_cholera)

# Créer un DataFrame pour visualiser les résultats
df_comparaison = pd.DataFrame({
    "Provinces attendues": provinces_cholera,
    "Présentes": [p in provinces_compile_cholera for p in provinces_cholera],
    "Manquantes": [p if p not in provinces_compile_cholera else "" for p in provinces_cholera]
})

# Résumé global
df_resume_completude = pd.DataFrame({
    "Total provinces attendues": [resultat_calcul["nb_attendus"]],
    "Provinces trouvées": [resultat_calcul["nb_reçus"]],
    "Complétude (%)": [resultat_calcul["completude_%"]],
    "Provinces manquantes": [", ".join(resultat_calcul["manquantes"])]
})

# Affichage
display(df_comparaison)
display(df_resume_completude)
# df_resume_completude.to_excel("LL_Cholera_completude_SE36.xlsx",sheet_name="Cholera_completude",index=False)


# ANALYSE

# In[ ]:


# Paramètres 
nom_maladie="Cholera"
semaine_epi_min=1
semaine_epi_max=52
annee_semaine_epi=2025
provinces_endemiques = ["Nord_kivu", "Sud_kivu", "Haut_katanga", "Haut_lomami","Tanganyika"]
provinces_epidemiques = ["Tshopo", "Maniema", "Kinshasa","Sankuru",
                        "Lualaba","Maindombe","Mongala","Lomami",
                        "Kasai_oriental","Equateur"
                        ]


# In[ ]:


df_analyse=df_sans_doublons.copy()
# Supprimer les autres colonnes inutiles
df_analyse=supprimer_colonnes_inutiles(df_analyse)


# In[ ]:


df_analyse=df_sans_doublons.copy()
# Filtre semaine et année epidémiomiologique
df_analyse_filtre_semaine = filtrer_par_semaine(
    df_analyse,
    colonnes_semaine="Num_semaine_epi",
    condition=df_analyse['Annee_epi'] == annee_semaine_epi
)


# In[ ]:


# Nettoyer les colonnes pour l'étude
colonnes_a_verifier = ['Sexe', 'Resultat_labo','Issue','Statut_vaccinal','Symptomes', 'Femme_enceinte', 'Degre_deshydratation','Hospitalisation','Prelevement','TDR_realise','TDR_Resultat']
df_analyse_filtre_semaine=clean_all_values(
    df_analyse_filtre_semaine, 
    cols=colonnes_a_verifier,
    case_option='capitalize', 
    remove_accents=True
)  
df_analyse_filtre_semaine[get_target_columns(df_analyse_filtre_semaine,colonnes_a_verifier)]


# In[ ]:


# Nombre de cas par province
colonnes_analyse_1=['Province_notification']
compter_par_plusieurs_categories(df_analyse_filtre_semaine,colonnes_analyse_1)


# In[ ]:


# TCD par province et semaine epi
df_semaine_epi=df_analyse_filtre_semaine.loc[df_analyse_filtre_semaine["Num_semaine_epi"]==semaine_epi_max]
tcd = tableau_croise_dynamique(
    df=df_semaine_epi,
    lignes="Province_notification",
    colonnes="Num_semaine_epi",
    valeurs="Nom_complet",
    aggfunc="count",
    fill_value=0,
    margins=True,
    margins_name="Total"
)
tcd


# In[ ]:


# Tranche d'age
colonnes_analyse_1=['Unite_age','Tranche_age']
cas_UniteAge_TrancheAge = compter_par_plusieurs_categories(df_analyse_filtre_semaine, colonnes_analyse_1)
# Filtrer les lignes où "Nombre de cas" > 0
cas_UniteAge_TrancheAge = cas_UniteAge_TrancheAge[cas_UniteAge_TrancheAge["Nombre de cas"] > 0]
cas_UniteAge_TrancheAge


# VISUALISATION 
# - Graphique

# In[ ]:


df_viz=df_analyse_filtre_semaine.copy()
# Filtre semaine et année epidémiomiologique
df_viz_filtre_semaine = filtrer_par_semaine(
    df_viz,
    colonnes_semaine="Num_semaine_epi",
)
# Parametres
df_provinces_semaines = df_viz_filtre_semaine.loc[
    (df_viz_filtre_semaine["Num_semaine_epi"] <=semaine_epi_max)]


# - Histogramme

# In[ ]:


# Histogramme empilé 
graph=plot_histogramme_groupe_interactif_empile(
    df_provinces_semaines,
    x_col='Num_semaine_epi',
    x_titre='Semaine épidémiologique',
    hue_col='Tranche_age',
    y_titre="Nombre de cas",
    titre=f"Évolution hebdomadaire des cas suspects investigués par tranche d’âge de {nom_maladie} en RDC (SE0{semaine_epi_min} à SE{semaine_epi_max})",
    rotation=45,
    annot=True,
    pas_x=1,
    bargap=0,
    bargroupgap=0.05,
    taille_fig = (1500, 700),
    x_trier=False
)


# In[ ]:


# Cas par chaque province
df_provinces_semaines_1=df=df_provinces_semaines.loc[df_provinces_semaines['Province_notification'].isin(provinces_endemiques)]
graphique_barres_facette(
    df=df_provinces_semaines,
    x_col='Num_semaine_epi',
    x_titre="Semaine épidémiologique",
    y_col='Province_notification',
    y_titre="Nombre de cas",
    facette_col='Province_notification',
    titre=f"Répartition des cas par province et semaine de {nom_maladie} en RDC (SE0{semaine_epi_min} à SE{semaine_epi_max})",
    taille_fig=(1500, 500),
    rotation=45,
    couleurs_personnalisees="black",
)


# - Courbe

# In[ ]:


# Cas par semaine épidémiologique par provinces individuelle
df_provinces_semaines_1 = df_provinces_semaines.loc[df_provinces_semaines['Num_semaine_epi']==semaine_epi_max]
plot_courbe_par_categories_plotly(
    df_provinces_semaines,
    colonne_x='Num_semaine_epi',
    colonne_y='Province_notification',
    titre=f"Evolution des cas de {nom_maladie} par semaine épidémiologique et par province de {nom_maladie} en RDC (SE0{semaine_epi_min} à SE{semaine_epi_max}) {annee_semaine_epi}",
    rotation=45,
    pas_x=1,
    annot=True,
    taille_fig=(1500, 500)
)


# In[ ]:


# Cas par semaine épidémiologique et province
plot_courbe_plotly(
    df_provinces_semaines,
    colonne='Num_semaine_epi',
    titre=f"Répartition des cas de {nom_maladie} par semaine épidémiologique en RDC (SE0{semaine_epi_min} à SE{semaine_epi_max})",
    pas_x=1,
    annot=True,
    taille_fig=(1500, 500)
)


# In[ ]:


# df_provinces_semaines[df_provinces_semaines["Num_semaine_epi"] > 34].to_excel("donnees_a_verifier.xlsx")


# In[ ]:


df_viz_filtre_semaine["Femme_enceinte"] = df_viz_filtre_semaine["Femme_enceinte"].str.lower()
df_viz_filtre_semaine["Hospitalisation"] = df_viz_filtre_semaine["Hospitalisation"].str.lower()
valeurs_courbe_col = {"Femme_enceinte": "oui", "Hospitalisation": "oui"}

plot_evolution_multi_auto(
    df=df_viz_filtre_semaine,
    col_x="Num_semaine_epi",
    courbe_col=["Femme_enceinte", "Hospitalisation"],
    valeurs_courbe_col=valeurs_courbe_col,
    titre=f"Évolution hebdomadaire {valeurs_courbe_col}",
    annot_x=True,
    annot_y=True,
    rotation=0,
    seuil_min=0,
    taille_fig=(1450, 600)
)


# - Camembert

# In[ ]:


# Partage des cas de Cholera par tranche d'âge et unité d'âge
plot_camembert_interactif(
    df_provinces_semaines,
    ['Unite_age','Tranche_age'],
    titre = f"Proportion des cas de {nom_maladie} par tranche d'âge et unité d'âge de la semaine épidémiologique en RDC (SE0{semaine_epi_min} à SE{semaine_epi_max})",
    seuil_min=0,
    afficher_legende=True,
    annot=True,
    taille_fig=(1400, 600)
)


# - Pyramide

# In[ ]:


# Pyramide
plot_pyramide_symetrique(
    df=df_provinces_semaines,
    col_categorie="Tranche_age",
    col_groupe="Sexe",
    valeurs_neg=["Masculin"],
    titre=f"Distribution par tranche d'âge et sexe des cas de {nom_maladie} en RDC (SE0{semaine_epi_min} à SE{semaine_epi_max})",
    seuil_min=10,
    croissant=False,
    afficher_signe_negatif_dans_label=False

)


# In[ ]:


# Pyramides par provinces de tranche d'âge et sexe
df_provinces_semaines_1=df=df_provinces_semaines.loc[df_provinces_semaines['Province_notification'].isin(provinces_endemiques)]
fig = graphique_pyramide_age(
    df=df_provinces_semaines,
    col_tranche='Tranche_age',     # ou Tranche_age_en_ans
    col_sexe='Sexe',
    col_valeur='Unite_age',
    valeurs_neg=["Masculin"],
    titre=f"Distribution par tranche d'âge et sexe des cas de {nom_maladie} en RDC (SE0{semaine_epi_min} à SE{semaine_epi_max})",
    seuil_min=10,
    croissant=False,
    afficher_signe_negatif_dans_label=False,
    facette_col='Province_notification',
    annot=True,
    couleurs_personnalisees={"Masculin": "#1a1e2b","Feminin": "Red"},
    taille_fig= (1500, 700),
    couleur_contour_facette="#777772"
)


# CODE INDIVIDU

# In[ ]:


# from dataminsante.database_pyramide import *
# col_date = ['Date_admission', 'Date_debut_maladie']
# col_prov = ['Province_notification', 'Province_provenance']
# col_zone = ['Zone_de_sante_notification', 'Zone_de_sante_provenance']
# pyramide = clean_database_pyramide()
# df_codes = generer_code_individus(
#     df=df_export,
#     colonne_date=col_date,
#     colonnes_province=col_prov,
#     colonnes_zone=col_zone,
#     nom_colonne_code='Code_individu',
#     database_pyramide=pyramide,
#     ignore_lignes_vides=True,
#     normaliser_colonnes=True,
#     afficher_erreurs_fusion=True,
#     ignorer_lignes_non_fusionnees=True,
#     supprimer_colonnes_ref=True,
#     retourner_rapport=True,
#     utiliser_matching_fluo=True,
#     seuil_similarite=0.92
# )

