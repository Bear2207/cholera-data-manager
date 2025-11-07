# -*- coding: utf-8 -*-
"""
Module : dataminsante.compilation.fichiers_nommage
--------------------------------------------------
Fonctions utilitaires pour générer, valider et analyser les noms
de fichiers épidémiologiques (listes linéaires, rapports, etc.).

Les conventions respectées :
    - <PROVINCE>_<ZONE>_<TYPE>_<MALADIE>.xlsx
    - <PROVINCE>_<TYPE>_<MALADIE>_<PERIODE>.xlsx
    - <PROVINCE>_<ZONE>_<TYPE>_<MALADIE>_<PERIODE>.csv
    - <PROVINCE>_<TYPE>_<MALADIE>_SE40.xlsx
    - Double underscore possible pour zone vide : "MD_LL__Rougeole_2024-05.xlsx"

Exemples :
    BAS_BASANKUSU_LL_Rougeole.xlsx
    BAS_LL_Rougeole_2025-07-27.xlsx
    TSH_LL_Cholera_SE40.xlsx
"""

import re
import logging
from datetime import datetime
from typing import Optional, Dict, List

# ------------------------------------------------------------
# Configuration du logger local
# ------------------------------------------------------------
logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

# ------------------------------------------------------------
# Constantes et configuration
# ------------------------------------------------------------
# Types de fichiers pris en charge
TYPES_FICHIERS_PAR_DEFAUT = ["LL", "RS"]

# Extension par défaut
EXTENSION_PAR_DEFAUT = "xlsx"

__all__ = [
    "generer_nom_fichier",
    "generer_nom_feuille",
    "est_nom_fichier_valide",
    "normaliser_zone_texte",
    "extraire_infos_nom_fichier",
]


# ------------------------------------------------------------
# Fonctions principales
# ------------------------------------------------------------
def generer_nom_fichier(
    province_code: str,
    zone: Optional[str] = None,
    type_fichier: str = "LL",
    maladie: str = "Rougeole",
    fusion: bool = False,
    extension: str = EXTENSION_PAR_DEFAUT,
    date: Optional[str] = None  # format "YYYY-MM-DD"
) -> str:
    """
    Génère un nom de fichier standardisé pour les fichiers épidémiologiques.

    Exemple :
        BAS_BASANKUSU_LL_Rougeole.xlsx
        BAS_LL_Rougeole_2025-07-27.xlsx

    Args:
        province_code: Code de la province (ex: "BAS").
        zone: Nom de la zone de santé (optionnel si fusion=True).
        type_fichier: Type de fichier ("LL" ou "RS").
        maladie: Nom de la maladie ("Rougeole", "Cholera"...).
        fusion: True si fichier fusionné (pas de zone).
        extension: Type d’extension du fichier ("xlsx", "csv"...).
        date: Date ISO facultative ("2025-07-27").

    Returns:
        Nom de fichier normalisé (str).
    """
    if fusion:
        if not province_code:
            raise ValueError("Le code province est requis pour un fichier fusionné.")
        nom = f"{province_code.upper()}_{type_fichier.upper()}_{maladie.capitalize()}"
    else:
        if not (province_code and zone):
            raise ValueError("Province et zone sont obligatoires pour un fichier non fusionné.")
        nom = f"{province_code.upper()}_{zone.upper()}_{type_fichier.upper()}_{maladie.capitalize()}"

    if date:
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("La date doit être au format 'YYYY-MM-DD'.")
        nom += f"_{date}"

    nom_complet = f"{nom}.{extension.lower()}"
    logger.debug(f"Nom de fichier généré : {nom_complet}")
    return nom_complet


def generer_nom_feuille(type_fichier: str = "LL", maladie: str = "Rougeole") -> str:
    """
    Génère un nom de feuille Excel standardisé.

    Exemple :
        generer_nom_feuille("LL", "Cholera") -> "LL_Cholera"
    """
    feuille = f"{type_fichier.upper()}_{maladie.capitalize()}"
    logger.debug(f"Nom de feuille généré : {feuille}")
    return feuille


def est_nom_fichier_valide(
    nom: str,
    types_fichiers: Optional[List[str]] = None
) -> bool:
    """
    Vérifie si un nom de fichier respecte la convention standard.

    Exemples valides :
        BAS_BASANKUSU_LL_Rougeole.xlsx
        BAS_LL_Rougeole_2025-07-27.csv
        BAS_LL_Rougeole_SE40.xlsx

    Args:
        nom: Nom de fichier à tester.
        types_fichiers: Liste des types autorisés (ex: ["LL", "RS"]).

    Returns:
        True si le nom est valide, False sinon.
    """
    types_fichiers = types_fichiers or TYPES_FICHIERS_PAR_DEFAUT
    types_pattern = "|".join(types_fichiers)
    pattern = rf"^[A-Z]{{3}}(_[A-Z0-9_-]+)?_({types_pattern})_[A-Z][a-zA-Zéèêôà\\s-]+(_\\d{{4}}(-\\d{{2}}(-\\d{{2}})?)?|_S[Ee]?\\d{{1,2}})?\\.(xlsx|csv)$"

    try:
        return bool(re.match(pattern, nom))
    except re.error as e:
        logger.error(f"Erreur dans le pattern de validation : {e}")
        return False


def normaliser_zone_texte(zone: str) -> str:
    """
    Normalise une chaîne représentant une zone (espaces, underscores, tirets).

    Exemples :
        'zone-de_sante ouest' -> 'Zone_De_Sante_Ouest'
        'basankusu' -> 'Basankusu'
    """
    if not isinstance(zone, str):
        return ""
    segments = re.split(r"[_\\-\\s]+", zone)
    return "_".join(s.capitalize() for s in segments if s)


def extraire_infos_nom_fichier(nom_fichier: str) -> Optional[Dict[str, Optional[str]]]:
    """
    Extrait les composantes d’un nom de fichier épidémiologique.

    Gère :
        - Province, Zone, Type, Maladie, Période (si présente)
        - Double underscore pour zone vide
        - Formats avec ou sans date, avec SE/semaine

    Args:
        nom_fichier: Nom du fichier (avec extension).

    Returns:
        dict : {
            "province": str,
            "zone": str | None,
            "type": str,
            "maladie": str,
            "periode": str | None
        } ou None si non conforme.
    """
    nom_sans_ext = nom_fichier.rsplit(".", 1)[0]

    # Liste des patterns supportés
    patterns = [
        # Province + type + __ + maladie (+ période)
        r"^(?P<province>[a-zA-Z]{1,3})_(?P<type>[A-Z]+)__(?P<maladie>[A-Z][a-zA-Zéèêôà\\s\\-_]+)(_(?P<periode>\\d{4}(-\\d{2}(-\\d{2})?|S[Ee]?\\d{1,2})))?$",

        # Province + zone + type + maladie + période
        r"^(?P<province>[a-zA-Z]{1,3})_(?P<zone>[A-Za-z0-9_\\-\\s]+)_(?P<type>[A-Z]+)_(?P<maladie>[A-Z][a-zA-Zéèêôà\\s\\-_]+)_(?P<periode>\\d{4}(-\\d{2}(-\\d{2})?)?|S[Ee]?\\d{1,2})$",

        # Province + zone + type + maladie
        r"^(?P<province>[a-zA-Z]{1,3})_(?P<zone>[A-Za-z0-9_\\-\\s]+)_(?P<type>[A-Z]+)_(?P<maladie>[A-Z][a-zA-Zéèêôà\\s\\-_]+)$",

        # Province + type + zone + maladie + période
        r"^(?P<province>[a-zA-Z]{1,3})_(?P<type>[A-Z]+)_(?P<zone>[A-Za-z0-9_\\-\\s]+)_(?P<maladie>[A-Z][a-zA-Zéèêôà\\s\\-_]+)_(?P<periode>\\d{4}(-\\d{2}(-\\d{2})?)?|S[Ee]?\\d{1,2})$",

        # Province + type + maladie + période
        r"^(?P<province>[a-zA-Z]{1,3})_(?P<type>[A-Z]+)_(?P<maladie>[A-Z][a-zA-Zéèêôà\\s\\-_]+)_(?P<periode>\\d{4}(-\\d{2}(-\\d{2})?)?|S[Ee]?\\d{1,2})$",

        # Province + type + maladie
        r"^(?P<province>[a-zA-Z]{1,3})_(?P<type>[A-Z]+)_(?P<maladie>[A-Z][a-zA-Zéèêôà\\s\\-_]+)$",
    ]

    for pattern in patterns:
        try:
            match = re.match(pattern, nom_sans_ext, re.IGNORECASE)
        except re.error as e:
            logger.error(f"Erreur regex sur le pattern : {e}")
            continue

        if match:
            groupes = match.groupdict()

            # Normalisations
            groupes["province"] = groupes["province"].lower()
            groupes["zone"] = (
                normaliser_zone_texte(groupes["zone"]) if groupes.get("zone") else None
            )
            groupes["maladie"] = groupes["maladie"].capitalize()

            # Nettoyage période
            periode = groupes.get("periode")
            if periode:
                # Harmonisation Sxx -> SExx
                if re.match(r"^s[eE]?\\d{1,2}$", periode, re.IGNORECASE):
                    periode = periode.upper()
                    if not periode.startswith("SE"):
                        periode = "SE" + periode[1:]
                    groupes["periode"] = periode

                # Validation date ISO (année, année-mois ou année-mois-jour)
                if re.match(r"^\\d{4}(-\\d{2}(-\\d{2})?)?$", periode):
                    try:
                        parts = periode.split("-")
                        y = int(parts[0])
                        m = int(parts[1]) if len(parts) > 1 else 1
                        d = int(parts[2]) if len(parts) > 2 else 1
                        datetime(y, m, d)
                    except Exception:
                        logger.warning(f"Date invalide détectée dans période : {periode} ({nom_fichier})")

            return groupes

    logger.warning(f"Nom fichier non conforme ou non reconnu : {nom_fichier}")
    return None


# ------------------------------------------------------------
# Tests rapides (exécution directe)
# ------------------------------------------------------------
if __name__ == "__main__":
    exemples = [
        "BAS_BASANKUSU_LL_Rougeole.xlsx",
        "BAS_LL_Rougeole_2025-07-27.xlsx",
        "TSH_LL_Cholera_SE40.xlsx",
        "MD_LL__Rougeole_2024-05.xlsx",
        "XYZ_RS_Covid19.csv",
    ]

    for nom in exemples:
        print(f"→ {nom}")
        print("  Valide :", est_nom_fichier_valide(nom))
        print("  Infos :", extraire_infos_nom_fichier(nom))
        print("-" * 60)
