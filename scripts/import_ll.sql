-- Table temporaire pour recevoir les données brutes (toutes colonnes en TEXT)
CREATE TEMP TABLE temp_ll (LIKE cas_ll INCLUDING ALL);
ALTER TABLE temp_ll ALTER COLUMN id DROP DEFAULT;
ALTER TABLE temp_ll ALTER COLUMN id DROP NOT NULL;

-- Copie depuis le CSV (adaptez le chemin)
\COPY temp_ll (n_epid_prov, n_epid, statut_a_l_arrivee, date_arrivee_malade, date_admission_au_ct, date_notification, date_investigation, date_debut_maladie, province_notification, zone_de_sante_notification, aire_de_sante_notification, semaine_epid, num_semaine_epid, annee_epid, nom_complet, sexe, age_annee, age_mois, age, unite_age, age_en_ans, tranche_age, tranche_age_en_ans, profession, province_provenance, zone_de_sante_provenance, aire_de_sante_provenance, adresse, symptomes, prise_antibiotique_avant_admission, nom_antibiotique, antecedents_morbides, femme_enceinte, degre_deshydratation, plan_de_deshydratation, hospitalisation, prelevement, date_prelevement, tdr_realise, tdr_resultat, tdr_archive, resultat_labo, resultat_labo_culture, serotype, nom_structure_realisant_le_tdr, resultat_labo_pcr, traitement_antibiotique, quantite_total_ringer_recue, quantite_total_sro_recue, ctc_utc, issue, date_sortie_au_ct, etat_sortie_malade, statut_vaccinal, nombre_dose, annee_vaccination, source_eventuelle_de_contamination, source_approvisionnement_en_eau, classification_finale, date_de_guerie, observation)
FROM '/tmp/ll_cholera_data.csv'
DELIMITER ',' CSV HEADER NULL '';

-- Insertion dans la table finale avec conversion
INSERT INTO cas_ll (
    n_epid_prov, n_epid, statut_a_l_arrivee, date_arrivee_malade, date_admission_au_ct,
    date_notification, date_investigation, date_debut_maladie,
    province_notification, zone_de_sante_notification, aire_de_sante_notification,
    semaine_epid, num_semaine_epid, annee_epid,
    nom_complet, sexe, age_annee, age_mois, age, unite_age, age_en_ans,
    tranche_age, tranche_age_en_ans, profession,
    province_provenance, zone_de_sante_provenance, aire_de_sante_provenance, adresse,
    symptomes, prise_antibiotique_avant_admission, nom_antibiotique,
    antecedents_morbides, femme_enceinte, degre_deshydratation, plan_de_deshydratation,
    hospitalisation, prelevement, date_prelevement,
    tdr_realise, tdr_resultat, tdr_archive, resultat_labo, resultat_labo_culture,
    serotype, nom_structure_realisant_le_tdr, resultat_labo_pcr,
    traitement_antibiotique, quantite_total_ringer_recue, quantite_total_sro_recue,
    ctc_utc, issue, date_sortie_au_ct, etat_sortie_malade,
    statut_vaccinal, nombre_dose, annee_vaccination,
    source_eventuelle_de_contamination, source_approvisionnement_en_eau,
    classification_finale, date_de_guerie, observation
)
SELECT
    n_epid_prov, n_epid, statut_a_l_arrivee,
    NULLIF(date_arrivee_malade,'')::DATE,
    NULLIF(date_admission_au_ct,'')::DATE,
    NULLIF(date_notification,'')::DATE,
    NULLIF(date_investigation,'')::DATE,
    NULLIF(date_debut_maladie,'')::DATE,
    province_notification, zone_de_sante_notification, aire_de_sante_notification,
    semaine_epid,
    NULLIF(num_semaine_epid,'')::FLOAT::INTEGER,
    NULLIF(annee_epid,'')::FLOAT::INTEGER,
    nom_complet, sexe,
    NULLIF(age_annee,'')::FLOAT,
    NULLIF(age_mois,'')::FLOAT,
    NULLIF(age,'')::FLOAT,
    unite_age,
    NULLIF(age_en_ans,'')::FLOAT,
    tranche_age, tranche_age_en_ans, profession,
    province_provenance, zone_de_sante_provenance, aire_de_sante_provenance,
    adresse, symptomes,
    prise_antibiotique_avant_admission, nom_antibiotique,
    antecedents_morbides, femme_enceinte, degre_deshydratation,
    plan_de_deshydratation, hospitalisation, prelevement,
    NULLIF(date_prelevement,'')::DATE,
    tdr_realise, tdr_resultat, tdr_archive, resultat_labo, resultat_labo_culture,
    serotype, nom_structure_realisant_le_tdr, resultat_labo_pcr,
    traitement_antibiotique,
    NULLIF(quantite_total_ringer_recue,'')::FLOAT,
    NULLIF(quantite_total_sro_recue,'')::FLOAT,
    ctc_utc, issue,
    NULLIF(date_sortie_au_ct,'')::DATE,
    etat_sortie_malade,
    statut_vaccinal,
    NULLIF(nombre_dose,'')::FLOAT::INTEGER,
    NULLIF(annee_vaccination,'')::FLOAT,
    source_eventuelle_de_contamination,
    source_approvisionnement_en_eau,
    classification_finale,
    NULLIF(date_de_guerie,'')::DATE,
    observation
FROM temp_ll
ON CONFLICT (n_epid, province_notification, num_semaine_epid, annee_epid) DO NOTHING;

-- Nettoyage
DROP TABLE temp_ll;