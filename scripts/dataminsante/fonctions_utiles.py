# -*- coding: utf-8 -*-

# dataminsante/fonctions_utiles.py
"""
dataminsante/fonctions_utiles.py

Module utilitaire regroupant :
- Logging configuré
- Ajout du chemin racine au PYTHONPATH
- Chemins de référence centralisés
- Affichage d'arborescence de dossier (amélioré)
- Analyse des dépendances internes des fichiers du projet
- Analyse avancée du code source :
  * Variables globales
  * Docstrings
  * Imports externes
  * Chemins codés en dur
  * Fonctions non utilisées
  * Arguments des fonctions

Usage typique :

    from dataminsante.fonctions_utiles import (
        get_logger,
        ajouter_racine_projet,
        CHEMIN_RACINE,
        CHEMIN_DATA,
        get_arborescence,
        analyser_dependances_projet,
        analyser_code_source
    )
"""

import sys
import os
import logging
import re
from pathlib import Path
import ast
from collections import defaultdict
from nbconvert import ScriptExporter
import nbformat
import shutil
import subprocess


# -------------------
# CONFIGURATION DU LOGGER
# -------------------

log_dir = Path(__file__).resolve().parents[1] / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
log_file_path = log_dir / "dataminsante.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file_path, mode='a', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def get_logger(name=None):
    """
    Récupère un logger configuré.
    """
    return logging.getLogger(name)


# --------------------------
# AJOUTER LA RACINE AU PATH
# --------------------------

def ajouter_racine_projet(profondeur: int = 2) -> None:
    """
    Ajoute la racine du projet au PYTHONPATH.
    """
    racine_projet = Path(__file__).resolve()
    for _ in range(profondeur):
        racine_projet = racine_projet.parent

    chemin = str(racine_projet)
    if chemin not in sys.path:
        sys.path.append(chemin)
        get_logger(__name__).info(f"✅ Chemin projet ajouté au PYTHONPATH : {chemin}")
    else:
        get_logger(__name__).info(f"ℹ️ Chemin déjà présent dans PYTHONPATH : {chemin}")


# --------------------------
# CHEMINS CENTRAUX DU PROJET
# --------------------------

CHEMIN_RACINE = Path(__file__).resolve().parents[1]
CHEMIN_DATA = CHEMIN_RACINE / "data"


# --------------------------
# AFFICHAGE DE L'ARBORESCENCE (amélioré)
# --------------------------

def get_arborescence(dossier, prefixe="", profondeur_max=None, niveau=0):
    """
    Génère l'arborescence textuelle du dossier.
    """
    if profondeur_max is not None and niveau > profondeur_max:
        return ""

    try:
        fichiers = sorted(os.listdir(dossier))
    except Exception as e:
        return f"Erreur : {e}"

    lignes = []
    for i, nom in enumerate(fichiers):
        chemin_complet = os.path.join(dossier, nom)
        est_dernier = (i == len(fichiers) - 1)
        prefixe_fichier = "└── " if est_dernier else "├── "
        lignes.append(f"{prefixe}{prefixe_fichier}{nom}")

        if os.path.isdir(chemin_complet):
            prefixe_sous = "    " if est_dernier else "│   "
            sous_arbo = get_arborescence(
                chemin_complet,
                prefixe=prefixe + prefixe_sous,
                profondeur_max=profondeur_max,
                niveau=niveau + 1
            )
            if sous_arbo:
                lignes.append(sous_arbo)
    return "\n".join(lignes)


# --------------------------
# SELECTION DES FICHIERS A ANALYSER
# --------------------------

def _lister_fichiers_py(racine, fichiers):
    """
    Résout les fichiers fournis ou liste tous les .py si None.
    """
    logger = get_logger(__name__)
    result = []

    if not fichiers:
        return sorted(racine.glob("*.py"))

    for f in fichiers:
        chemin_f = Path(f)
        if not chemin_f.is_absolute():
            chemin_f = racine / chemin_f
        if chemin_f.exists() and chemin_f.suffix == ".py":
            result.append(chemin_f)
        else:
            logger.warning(f"⚠️ Ignoré (introuvable ou pas .py) : {f}")
    return result


# --------------------------
# ANALYSE DES DÉPENDANCES INTERNES
# --------------------------

def analyser_dependances_projet(fichiers=None):
    """
    🔎 Analyse statique des imports internes entre fichiers Python du projet.
    """
    logger = get_logger(__name__)
    logger.info("📦 Démarrage de l'analyse des dépendances internes du projet")

    racine = CHEMIN_RACINE / "dataminsante"
    fichiers_a_analyser = _lister_fichiers_py(racine, fichiers)

    independants = []
    dependants = {}

    for chemin in fichiers_a_analyser:
        module = chemin.stem
        depends_on = set()

        try:
            with open(chemin, encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("#"):
                        continue
                    m1 = re.match(r'^import\s+dataminsante\.([a-zA-Z0-9_]+)', line)
                    m2 = re.match(r'^from\s+dataminsante\.([a-zA-Z0-9_]+)', line)
                    if m1:
                        depends_on.add(m1.group(1))
                    elif m2:
                        depends_on.add(m2.group(1))
        except Exception as e:
            logger.error(f"❌ Erreur lecture {chemin}: {e}")
            continue

        if depends_on:
            dependants[module] = sorted(depends_on)
        else:
            independants.append(module)

    logger.info("✅ Résultat de l'analyse des dépendances :\n")

    logger.info("🟢 Modules indépendants :")
    for mod in sorted(independants):
        logger.info(f"  - {mod}")

    logger.info("\n🟠 Modules dépendants :")
    for mod, deps in dependants.items():
        logger.info(f"  - {mod} dépend de : {', '.join(deps)}")

    logger.info("\n✨ Analyse terminée.")


# --------------------------
# ANALYSE COMPLÈTE DU CODE SOURCE
# --------------------------

def analyser_code_source(
    fichiers=None,
    afficher_variables_globales=False,
    afficher_docstrings=False,
    afficher_imports_externes=False,
    afficher_liens_codedur=False,
    afficher_fonctions_non_utilisees=False,
    afficher_arguments_fonctions=False,
):
    """
    Analyse statique des fichiers Python du projet avec options détaillées.
    """
    logger = get_logger(__name__)
    racine = CHEMIN_RACINE / "dataminsante"
    logger.info("🔎 Analyse du code source avec options :")
    logger.info(f"  Variables globales           : {afficher_variables_globales}")
    logger.info(f"  Docstrings                   : {afficher_docstrings}")
    logger.info(f"  Imports externes             : {afficher_imports_externes}")
    logger.info(f"  Chemins codés en dur         : {afficher_liens_codedur}")
    logger.info(f"  Fonctions non utilisées      : {afficher_fonctions_non_utilisees}")
    logger.info(f"  Arguments des fonctions      : {afficher_arguments_fonctions}")

    fichiers_a_analyser = _lister_fichiers_py(racine, fichiers)
    fonctions_definies = defaultdict(set)
    fonctions_utilisees = defaultdict(set)

    for chemin in fichiers_a_analyser:
        module = chemin.stem
        logger.info(f"\n📄 Module analysé : {module}")
        try:
            with open(chemin, encoding='utf-8') as f:
                source = f.read()
            tree = ast.parse(source)
        except Exception as e:
            logger.error(f"❌ Erreur parsing {module}: {e}")
            continue

        if afficher_variables_globales:
            vars_globales = [
                n.targets[0].id for n in ast.walk(tree)
                if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)
            ]
            logger.info(f"  📄 Variables globales : {vars_globales if vars_globales else 'Aucune'}")

        if afficher_docstrings:
            doc_mod = ast.get_docstring(tree)
            logger.info(f"  🏷️ Docstring module : {repr(doc_mod) if doc_mod else 'Aucune'}")

            for cls in [n for n in tree.body if isinstance(n, ast.ClassDef)]:
                logger.info(f"  🏷️ Classe {cls.name} docstring : {repr(ast.get_docstring(cls) or 'Aucune')}")

            for func in [n for n in tree.body if isinstance(n, ast.FunctionDef)]:
                logger.info(f"  🏷️ Fonction {func.name} docstring : {repr(ast.get_docstring(func) or 'Aucune')}")

        if afficher_imports_externes:
            imports_ext = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports_ext.update(alias.name.split('.')[0] for alias in node.names if not alias.name.startswith('dataminsante'))
                elif isinstance(node, ast.ImportFrom) and node.module:
                    if not node.module.startswith('dataminsante'):
                        imports_ext.add(node.module.split('.')[0])
            logger.info(f"  📦 Imports externes : {sorted(imports_ext) if imports_ext else 'Aucun'}")

        if afficher_liens_codedur:
            pattern = re.compile(r'["\']((?:[A-Za-z]:)?[\\/][^"\']+)["\']')
            liens = pattern.findall(source)
            logger.info(f"  🔗 Chemins codés en dur : {liens if liens else 'Aucun'}")

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                fonctions_definies[module].add(node.name)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    fonctions_utilisees[module].add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    fonctions_utilisees[module].add(node.func.attr)

        if afficher_arguments_fonctions:
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    args = [a.arg for a in node.args.args]
                    logger.info(f"  ⚙️ Fonction '{node.name}' arguments : {args if args else 'Aucun'}")

    if afficher_fonctions_non_utilisees:
        logger.info("\n🔎 Fonctions potentiellement non utilisées :")
        for module, defs in fonctions_definies.items():
            unused = defs - fonctions_utilisees.get(module, set())
            if unused:
                logger.info(f"  ⚠️ Module {module} : {sorted(unused)}")
            else:
                logger.info(f"  ✅ Module {module} : Toutes les fonctions sont utilisées.")

    logger.info("\n✨ Analyse complète terminée.")


# --------------------------
# CONVERTIR UN NOTEBOOK EN SCRIPT PYTHON
# --------------------------

def convertir_ipynb_en_py(fichier_ipynb, fichier_py=None):
    """
    Convertit un notebook Jupyter (.ipynb) en script Python (.py).

    Args:
        fichier_ipynb (str): chemin du fichier .ipynb source.
        fichier_py (str, optionnel): chemin du fichier .py de sortie.
            Si None, prend le même nom que fichier_ipynb avec extension .py.

    Returns:
        str: chemin du fichier .py généré.

    Raises:
        FileNotFoundError: si le fichier_ipynb n'existe pas.
        Exception: pour d'autres erreurs.
    """
    if not os.path.exists(fichier_ipynb):
        raise FileNotFoundError(f"Fichier introuvable: {fichier_ipynb}")

    if fichier_py is None:
        fichier_py = os.path.splitext(fichier_ipynb)[0] + ".py"

    try:
        with open(fichier_ipynb, 'r', encoding='utf-8') as f:
            notebook = nbformat.read(f, as_version=4)

        exporter = ScriptExporter()
        script, _ = exporter.from_notebook_node(notebook)

        with open(fichier_py, 'w', encoding='utf-8') as f:
            f.write(script)

        return fichier_py

    except Exception as e:
        raise Exception(f"Erreur lors de la conversion : {e}")


# --------------------------
# SUPPRIMER __pycache__ ET .pyc
# --------------------------
# clean_cache.py
import os
import shutil

def supprimer_pycache_et_pyc(base_dir="."):
    for root, dirs, files in os.walk(base_dir):
        for nom_dir in dirs:
            if nom_dir == "__pycache__":
                chemin = os.path.join(root, nom_dir)
                print(f"Suppression : {chemin}")
                shutil.rmtree(chemin)
        for fichier in files:
            if fichier.endswith(".pyc"):
                chemin = os.path.join(root, fichier)
                print(f"Suppression : {chemin}")
                os.remove(chemin)
                
# clean_pyc_files.py
def supprimer_pyc_seulement(base_dir="."):
    for root, dirs, files in os.walk(base_dir):
        for fichier in files:
            if fichier.endswith(".pyc"):
                chemin = os.path.join(root, fichier)
                print(f"Suppression : {chemin}")
                os.remove(chemin)



# --------------------------
# Créer un fichier requirements
# --------------------------
def conda_to_requirements(output_file="requirements.txt"):
    try:
        # Récupérer la sortie de "conda list"
        result = subprocess.run(
            ["conda", "list"],
            capture_output=True,
            text=True,
            check=True
        )

        lignes = result.stdout.splitlines()
        packages = []

        for ligne in lignes:
            # ignorer les commentaires et en-têtes
            if ligne.startswith("#") or not ligne.strip():
                continue

            parts = ligne.split()
            if len(parts) >= 2:
                package, version = parts[0], parts[1]

                # Éviter les entrées bizarres (parfois "@" ou "<pip>")
                if package and version[0].isdigit():
                    packages.append(f"{package}=={version}")

        # écrire dans le fichier requirements.txt
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(packages))

        print(f"✅ Fichier {output_file} généré avec {len(packages)} packages.")

    except subprocess.CalledProcessError as e:
        print("❌ Erreur lors de l'exécution de conda list :", e)
    except Exception as e:
        print("❌ Erreur :", e)


if __name__ == "__main__":
    conda_to_requirements()

