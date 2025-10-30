# dataminsante/database_connexion.py
import os
import re
import logging
from pathlib import Path
import pandas as pd
import pyodbc
import psycopg2
from psycopg2 import OperationalError
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from typing import List


# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Connexion Access
def connecter_access(fichier_accdb):
    """
    Connexion à une base Access (.accdb ou .mdb).
    Retourne un objet connexion pyodbc ou None en cas d'erreur.
    Vérifie que le pilote ODBC Access est disponible (nécessite 64 bits si Python est 64 bits).
    """
    chemin_complet = Path(fichier_accdb).resolve()
    pilote_requis = "Microsoft Access Driver (*.mdb, *.accdb)"

    # Vérifier si le pilote est disponible
    pilotes = pyodbc.drivers()
    if pilote_requis not in pilotes:
        logger.error(f"❌ Pilote ODBC '{pilote_requis}' introuvable. Python est probablement en 64 bits "
                     f"et le pilote Access est en 32 bits.")
        logger.error("💡 Solutions : installer AccessDatabaseEngine 64 bits OU utiliser Python 32 bits.")
        return None

    conn_str = (
        fr"DRIVER={{{pilote_requis}}};"
        f"DBQ={chemin_complet};"
    )

    logger.info(f"🔗 Tentative de connexion à Access : {chemin_complet}")
    try:
        conn = pyodbc.connect(conn_str)
        logger.info("✅ Connexion Access réussie.")
        return conn
    except Exception as e:
        logger.error(f"❌ Erreur de connexion Access : {e}")
        return None

# Connexion PostgreSQL
def connecter_postgres(
    host="localhost", 
    database="nom_base", 
    user="nom_utilisateur",
    password="mot_de_passe", 
    port=5432
):
    """
    Connexion à une base PostgreSQL.
    Retourne un objet connexion psycopg2 ou None en cas d'erreur.
    """
    try:
        conn = psycopg2.connect(host=host, database=database, user=user, password=password, port=port)
        logger.info("✅ Connexion PostgreSQL réussie.")
        return conn
    except OperationalError as e:
        logger.error(f"❌ Erreur de connexion PostgreSQL : {e}")
        return None

# Connexion Drive Google
    """
    Ex.
    lien = "https://drive.google.com/drive/folders/17vj75nkYGIBUyi_HDHgElZPlhFhrx2M_?usp=drive_link"
    df_fichiers = parcourir_dossier_drive(lien, 'client_secrets.json')
    
    """
def extraire_id_dossier_drive(lien_drive):
    """
    Extrait l'ID du dossier Google Drive à partir d'un lien complet.

    Args:
        lien_drive (str): URL complète du dossier Google Drive.

    Returns:
        str: ID du dossier extrait du lien.

    Raises:
        ValueError: Si l'ID ne peut pas être extrait.
    """
    match = re.search(r'/folders/([a-zA-Z0-9_-]+)', lien_drive)
    if match:
        return match.group(1)
    else:
        raise ValueError("Lien Drive invalide ou ID introuvable")

def authentifier_drive(chemin_client_secrets='client_secrets.json', fichier_credentials='mycreds.txt'):
    """
    Authentifie l'utilisateur auprès de Google Drive via PyDrive2 en utilisant OAuth 2.0.
    Supporte la gestion du token avec cache pour éviter les authentifications répétées.

    Args:
        chemin_client_secrets (str): Chemin vers le fichier client_secrets.json.
        fichier_credentials (str): Chemin vers le fichier de sauvegarde des credentials OAuth.

    Returns:
        GoogleDrive: Objet GoogleDrive authentifié.

    Raises:
        FileNotFoundError: Si le fichier client_secrets.json est introuvable.
    """
    if not os.path.exists(chemin_client_secrets):
        raise FileNotFoundError(
            f"ERREUR : Le fichier '{chemin_client_secrets}' est introuvable.\n"
            "Crée-le via Google Cloud Console et place-le dans le dossier du script."
        )
    gauth = GoogleAuth()
    gauth.LoadClientConfigFile(chemin_client_secrets)

    if os.path.exists(fichier_credentials):
        gauth.LoadCredentialsFile(fichier_credentials)

    if gauth.credentials is None:
        try:
            gauth.CommandLineAuth()
        except Exception:
            gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        gauth.Refresh()
    else:
        gauth.Authorize()

    gauth.SaveCredentialsFile(fichier_credentials)
    return GoogleDrive(gauth)

def lister_fichiers_dossier(drive, folder_id, max_results=100):
    """
    Liste les fichiers d'un dossier Google Drive (y compris dossiers partagés) sans les télécharger.

    Args:
        drive (GoogleDrive): Objet GoogleDrive authentifié.
        folder_id (str): ID du dossier Google Drive à parcourir.
        max_results (int): Nombre maximal de fichiers à récupérer (par défaut 100).

    Returns:
        pandas.DataFrame: DataFrame contenant les métadonnées des fichiers listés
                          avec colonnes ['title', 'id', 'mimeType', 'createdDate', 'modifiedDate', 'fileSize'].
        DataFrame vide en cas d'erreur ou dossier vide.
    """
    query = f"'{folder_id}' in parents and trashed=false"
    try:
        file_list = drive.ListFile({
            'q': query,
            'maxResults': max_results,
            'supportsAllDrives': True,
            'includeItemsFromAllDrives': True
        }).GetList()
    except Exception as e:
        logger.error(f"Impossible de lister les fichiers : {e}")
        return pd.DataFrame()

    if not file_list:
        logger.info("Aucun fichier trouvé dans ce dossier.")
        return pd.DataFrame()

    records = []
    for f in file_list:
        records.append({
            'title': f['title'],
            'id': f['id'],
            'mimeType': f['mimeType'],
            'createdDate': f.get('createdDate'),
            'modifiedDate': f.get('modifiedDate'),
            'fileSize': f.get('fileSize')
        })

    logger.info(f"{len(records)} fichier(s) trouvé(s) dans le dossier {folder_id}.")
    return pd.DataFrame(records)

def parcourir_dossier_drive(lien_drive, chemin_client_secrets='client_secrets.json'):
    """
    Authentifie, extrait l'ID du dossier Google Drive depuis un lien, puis liste les fichiers du dossier.

    Args:
        lien_drive (str): URL complète du dossier Google Drive partagé.
        chemin_client_secrets (str): Chemin vers le fichier client_secrets.json.

    Returns:
        pandas.DataFrame: DataFrame contenant la liste des fichiers du dossier avec leurs métadonnées.
    """
    logger.info("Authentification en cours...")
    drive = authentifier_drive(chemin_client_secrets)

    logger.info("Extraction de l'ID du dossier...")
    folder_id = extraire_id_dossier_drive(lien_drive)

    logger.info("Parcours du dossier à distance...")
    df = lister_fichiers_dossier(drive, folder_id)

    return df


def telecharger_fichier_drive(drive, file_id, chemin_local):
    """
    Télécharge un fichier Google Drive par son ID vers un chemin local.
    """
    try:
        f = drive.CreateFile({'id': file_id})
        f.GetContentFile(chemin_local)
        logger.info(f"✅ Fichier téléchargé : {chemin_local}")
    except Exception as e:
        logger.error(f"❌ Erreur de téléchargement : {e}")

def lister_et_telecharger_drive(
    drive,
    folder_id: str,
    motif_fichier: str,
    dossier_local: str
) -> List[str]:
    """
    Parcourt récursivement un dossier Drive (via son ID), télécharge
    tous les fichiers qui matchent le motif donné.

    Args:
        drive: Objet authentifié (GoogleDrive).
        folder_id: ID du dossier racine.
        motif_fichier: Motif glob (ex: '*_LL_Rougeole*.xlsx')
        dossier_local: Chemin local où sauvegarder les fichiers.

    Returns:
        Liste des chemins locaux téléchargés.
    """
    from pathlib import Path
    import fnmatch
    downloaded = []

    Path(dossier_local).mkdir(exist_ok=True)

    # 1. Lister le contenu du dossier racine
    df_items = lister_fichiers_dossier(drive, folder_id)
    if df_items.empty:
        logger.warning(f"Aucun item trouvé dans le dossier ID={folder_id}")
        return downloaded

    # 2. Parcourir les sous-dossiers
    sous_dossiers = df_items[df_items["mimeType"] == "application/vnd.google-apps.folder"]

    for _, row in sous_dossiers.iterrows():
        province_id = row["id"]
        province_nom = row["title"]

        logger.info(f"🔍 Province : {province_nom}")

        df_fichiers = lister_fichiers_dossier(drive, province_id)

        if df_fichiers.empty:
            continue

        # Filtrer sur le motif
        fichiers_match = df_fichiers[
            df_fichiers["title"].apply(lambda x: fnmatch.fnmatch(x, motif_fichier))
        ]

        for _, fichier in fichiers_match.iterrows():
            nom_fichier = fichier["title"]
            file_id = fichier["id"]
            chemin_local = os.path.join(dossier_local, nom_fichier)
            try:
                telecharger_fichier_drive(drive, file_id, chemin_local)
                logger.info(f"✅ Téléchargé : {chemin_local}")
                downloaded.append(chemin_local)
            except Exception as e:
                logger.error(f"❌ Erreur téléchargement {nom_fichier} : {e}")

    return downloaded