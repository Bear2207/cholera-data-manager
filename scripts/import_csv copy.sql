-- Script pour importer les données CSV dans la table cas_maladie
-- Assurez-vous que le fichier CSV est accessible depuis le conteneur PostgreSQL
-- et que le chemin est correct.
-- executé dans le conteneur postgres via psql -U bearing -d maladie_db -f /scripts/import_csv.sql

docker exec -it cousp_DB psql -U bearing -d ids_db_2021

\copy cas_maladie(pays, province, zone_sante, population, num_semaine, debut_semaine, maladie, cas_total, deces_total, letalite, taux_attaque)
FROM '/db/data/donnees_maladie.csv'
DELIMITER ',' CSV HEADER;


-- Import des données Cholera
\copy cholera_cas (
    provenance, n_epid_prov, n_epid, statut_a_l_arrivee,
    date_arrivee_malade, date_admission, date_notification,
    date_investigation, date_debut_maladie, province_notification,
    zone_de_sante_notification, aire_de_sante_notification, semaine_epid,
    num_semaine_epi, annee_epi, nom_complet, sexe, age_annee,
    age_mois, age, unite_age, tranche_age, tranche_age_en_ans, profession,
    province_provenance, zone_de_sante_provenance, aire_de_sante_provenance,
    adresse, symptomes, prise_antibiotique_avant_admission, nom_antibiotique,
    antecedents_morbides, femme_enceinte, degre_deshydratation,
    plan_de_deshydratation, hospitalisation, prelevement, date_prelevement,
    tdr_realise, tdr_resultat, resultat_labo, resultat_labo_culture,
    serotype, nom_structure_realisant_le_tdr, resultat_labo_pcr,
    traitement_antibiotique, quantite_total_ringer_recue,
    quantite_total_sro_recue, ctc_utc, issue, date_de_sortie_malade,
    etat_sortie_malade, statut_vaccinal, nombre_dose, annee_vaccination,
    source_eventuelle_de_contamination, source_approvisionnement_en_eau,
    classification_finale, date_de_guerie, observation
) FROM '/db/data/cholera_data_compiled.csv' WITH CSV HEADER;

-- Statistiques après import
SELECT 
    'Cholera' as dataset,
    COUNT(*) as total_cas,
    COUNT(DISTINCT province_notification) as provinces,
    MIN(date_admission) as date_debut,
    MAX(date_admission) as date_fin
FROM cholera_cas;