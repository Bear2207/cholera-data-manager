import logging
from sqlalchemy import text

DEFAULT_PAYS = 'RDC'
logger = logging.getLogger(__name__)

def sync_ids_lookups(engine):
    with engine.begin() as conn:
        logger.info("Synchronisation des tables de référence pour IDS...")
        conn.execute(text("""
            INSERT INTO cholera.pays (nom)
            SELECT DISTINCT NULLIF(trim(both from pays), '')
            FROM cholera.cas_maladie
            WHERE pays IS NOT NULL AND trim(both from pays) <> ''
            ON CONFLICT (nom) DO NOTHING
        """))
        conn.execute(text("""
            INSERT INTO cholera.province (pays_id, nom)
            SELECT DISTINCT p.id, NULLIF(trim(both from province), '')
            FROM cholera.cas_maladie cm
            JOIN cholera.pays p ON trim(lower(cm.pays)) = trim(lower(p.nom))
            WHERE cm.province IS NOT NULL AND trim(both from cm.province) <> ''
            ON CONFLICT (pays_id, nom) DO NOTHING
        """))
        conn.execute(text("""
            INSERT INTO cholera.zone_sante (province_id, nom)
            SELECT DISTINCT pr.id, NULLIF(trim(both from zone_sante), '')
            FROM cholera.cas_maladie cm
            JOIN cholera.province pr ON trim(lower(cm.province)) = trim(lower(pr.nom))
            JOIN cholera.pays p ON pr.pays_id = p.id AND trim(lower(cm.pays)) = trim(lower(p.nom))
            WHERE cm.zone_sante IS NOT NULL AND trim(both from cm.zone_sante) <> ''
            ON CONFLICT (province_id, nom) DO NOTHING
        """))
        conn.execute(text("""
            INSERT INTO cholera.maladie (nom)
            SELECT DISTINCT NULLIF(trim(both from maladie), '')
            FROM cholera.cas_maladie
            WHERE maladie IS NOT NULL AND trim(both from maladie) <> ''
            ON CONFLICT (nom) DO NOTHING
        """))
        # Mise à jour des IDs
        conn.execute(text("""
            UPDATE cholera.cas_maladie cm
            SET pays_id = p.id
            FROM cholera.pays p
            WHERE cm.pays IS NOT NULL AND trim(lower(cm.pays)) = trim(lower(p.nom))
        """))
        conn.execute(text("""
            UPDATE cholera.cas_maladie cm
            SET province_id = pr.id
            FROM cholera.province pr
            JOIN cholera.pays p ON pr.pays_id = p.id
            WHERE cm.province IS NOT NULL
              AND trim(lower(cm.province)) = trim(lower(pr.nom))
              AND trim(lower(cm.pays)) = trim(lower(p.nom))
        """))
        conn.execute(text("""
            UPDATE cholera.cas_maladie cm
            SET zone_sante_id = z.id
            FROM cholera.zone_sante z
            JOIN cholera.province pr ON z.province_id = pr.id
            JOIN cholera.pays p ON pr.pays_id = p.id
            WHERE cm.zone_sante IS NOT NULL
              AND trim(lower(cm.zone_sante)) = trim(lower(z.nom))
              AND trim(lower(cm.province)) = trim(lower(pr.nom))
              AND trim(lower(cm.pays)) = trim(lower(p.nom))
        """))
        conn.execute(text("""
            UPDATE cholera.cas_maladie cm
            SET maladie_id = m.id
            FROM cholera.maladie m
            WHERE cm.maladie IS NOT NULL AND trim(lower(cm.maladie)) = trim(lower(m.nom))
        """))
        logger.info("Synchronisation IDS terminée.")

def sync_ll_lookups(engine):
    with engine.begin() as conn:
        logger.info("Synchronisation des tables de référence pour LL...")
        conn.execute(text("""
            INSERT INTO cholera.pays (nom)
            VALUES (:pays)
            ON CONFLICT (nom) DO NOTHING
        """), {'pays': DEFAULT_PAYS})
        conn.execute(text("""
            INSERT INTO cholera.province (pays_id, nom)
            SELECT DISTINCT p.id, name
            FROM (
                SELECT NULLIF(trim(both from province_notification), '') AS name FROM cholera.cas_ll
                UNION
                SELECT NULLIF(trim(both from province_provenance), '') AS name FROM cholera.cas_ll
            ) sub
            JOIN cholera.pays p ON trim(lower(p.nom)) = trim(lower(:pays))
            WHERE name IS NOT NULL
            ON CONFLICT (pays_id, nom) DO NOTHING
        """), {'pays': DEFAULT_PAYS})
        conn.execute(text("""
            WITH zone_names AS (
                SELECT DISTINCT NULLIF(trim(both from zone_de_sante_notification), '') AS nom,
                       NULLIF(trim(both from province_notification), '') AS province_name
                FROM cholera.cas_ll
                UNION
                SELECT DISTINCT NULLIF(trim(both from zone_de_sante_provenance), '') AS nom,
                       NULLIF(trim(both from province_provenance), '') AS province_name
                FROM cholera.cas_ll
            )
            INSERT INTO cholera.zone_sante (province_id, nom)
            SELECT DISTINCT pr.id, zn.nom
            FROM zone_names zn
            JOIN cholera.province pr ON trim(lower(pr.nom)) = trim(lower(zn.province_name))
            JOIN cholera.pays p ON pr.pays_id = p.id AND trim(lower(p.nom)) = trim(lower(:pays))
            WHERE zn.nom IS NOT NULL AND zn.province_name IS NOT NULL
            ON CONFLICT (province_id, nom) DO NOTHING
        """), {'pays': DEFAULT_PAYS})
        lookups = [
            ('sexe', 'sexe'), ('unite_age', 'unite_age'), ('hospitalisation', 'hospitalisation_status'),
            ('prelevement', 'prelevement_status'), ('tdr_realise', 'tdr_realise_status'),
            ('tdr_resultat', 'tdr_resultat_status'), ('resultat_labo', 'resultat_labo_status'),
            ('resultat_labo_culture', 'resultat_labo_culture_status'), ('resultat_labo_pcr', 'resultat_labo_pcr_status'),
            ('issue', 'issue'), ('statut_vaccinal', 'statut_vaccinal_status'),
            ('classification_finale', 'classification_finale')
        ]
        for source_col, lookup_table in lookups:
            conn.execute(text(f"""
                INSERT INTO cholera.{lookup_table} (nom)
                SELECT DISTINCT NULLIF(trim(both from {source_col}::text), '')
                FROM cholera.cas_ll
                WHERE {source_col} IS NOT NULL AND trim(both from {source_col}::text) <> ''
                ON CONFLICT (nom) DO NOTHING
            """))
        # Mise à jour des IDs
        conn.execute(text("""
            UPDATE cholera.cas_ll cl
            SET province_notification_id = pr.id
            FROM cholera.province pr
            JOIN cholera.pays p ON pr.pays_id = p.id
            WHERE cl.province_notification IS NOT NULL
              AND trim(lower(cl.province_notification)) = trim(lower(pr.nom))
              AND trim(lower(p.nom)) = trim(lower(:pays))
        """), {'pays': DEFAULT_PAYS})
        conn.execute(text("""
            UPDATE cholera.cas_ll cl
            SET province_provenance_id = pr.id
            FROM cholera.province pr
            JOIN cholera.pays p ON pr.pays_id = p.id
            WHERE cl.province_provenance IS NOT NULL
              AND trim(lower(cl.province_provenance)) = trim(lower(pr.nom))
              AND trim(lower(p.nom)) = trim(lower(:pays))
        """), {'pays': DEFAULT_PAYS})
        conn.execute(text("""
            UPDATE cholera.cas_ll cl
            SET zone_de_sante_notification_id = z.id
            FROM cholera.zone_sante z
            JOIN cholera.province pr ON z.province_id = pr.id
            JOIN cholera.pays p ON pr.pays_id = p.id
            WHERE cl.zone_de_sante_notification IS NOT NULL
              AND trim(lower(cl.zone_de_sante_notification)) = trim(lower(z.nom))
              AND cl.province_notification IS NOT NULL
              AND trim(lower(cl.province_notification)) = trim(lower(pr.nom))
              AND trim(lower(p.nom)) = trim(lower(:pays))
        """), {'pays': DEFAULT_PAYS})
        conn.execute(text("""
            UPDATE cholera.cas_ll cl
            SET zone_de_sante_provenance_id = z.id
            FROM cholera.zone_sante z
            JOIN cholera.province pr ON z.province_id = pr.id
            JOIN cholera.pays p ON pr.pays_id = p.id
            WHERE cl.zone_de_sante_provenance IS NOT NULL
              AND trim(lower(cl.zone_de_sante_provenance)) = trim(lower(z.nom))
              AND cl.province_provenance IS NOT NULL
              AND trim(lower(cl.province_provenance)) = trim(lower(pr.nom))
              AND trim(lower(p.nom)) = trim(lower(:pays))
        """), {'pays': DEFAULT_PAYS})
        for source_col, lookup_table in lookups:
            dest_col = f'{source_col}_id'
            if source_col == 'classification_finale':
                dest_col = 'classification_finale_id'
            elif source_col == 'statut_vaccinal':
                dest_col = 'statut_vaccinal_id'
            elif source_col == 'hospitalisation':
                dest_col = 'hospitalisation_id'
            elif source_col == 'prelevement':
                dest_col = 'prelevement_id'
            elif source_col == 'unite_age':
                dest_col = 'unite_age_id'
            elif source_col == 'tdr_realise':
                dest_col = 'tdr_realise_id'
            elif source_col == 'tdr_resultat':
                dest_col = 'tdr_resultat_id'
            elif source_col == 'resultat_labo':
                dest_col = 'resultat_labo_id'
            elif source_col == 'resultat_labo_culture':
                dest_col = 'resultat_labo_culture_id'
            elif source_col == 'resultat_labo_pcr':
                dest_col = 'resultat_labo_pcr_id'
            elif source_col == 'issue':
                dest_col = 'issue_id'
            elif source_col == 'sexe':
                dest_col = 'sexe_id'
            conn.execute(text(f"""
                UPDATE cholera.cas_ll cl
                SET {dest_col} = lt.id
                FROM cholera.{lookup_table} lt
                WHERE cl.{source_col} IS NOT NULL
                                    AND trim(lower(cl.{source_col}::text)) = trim(lower(lt.nom))
            """))
        logger.info("Synchronisation LL terminée.")