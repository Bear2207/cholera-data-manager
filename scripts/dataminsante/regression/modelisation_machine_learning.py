# -*- coding: utf-8 -*-
# dataminsante/modelisation_machine_learning.py

import pandas as pd
import logging
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OrdinalEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.metrics import classification_report, confusion_matrix
import joblib
from typing import List, Tuple, Optional

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def recuperer_entrees_et_cible(
    df: pd.DataFrame,
    colonne_cible: str,
    variables_explicatives: Optional[List[str]] = None
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Sépare le DataFrame en deux parties : les variables explicatives (X)
    et la variable cible (y) à prédire.

    Paramètres :
    -----------
    df : pd.DataFrame
        Le DataFrame contenant les données.

    colonne_cible : str
        Nom de la colonne cible à prédire.

    variables_explicatives : List[str], optionnel
        Liste des colonnes à utiliser comme variables explicatives.
        Si None, toutes les colonnes sauf la cible sont utilisées.

    Retour :
    -------
    Tuple[pd.DataFrame, pd.Series]
        - X : DataFrame des variables explicatives
        - y : Series de la variable cible
    """
    if variables_explicatives is None:
        X = df.drop(columns=[colonne_cible])
    else:
        X = df[variables_explicatives]
    y = df[colonne_cible]
    return X, y


def preparer_variables_explicatives(
    df: pd.DataFrame,
    variables_explicatives: List[str],
    verbose: bool = True
) -> pd.DataFrame:
    """
    Prépare les variables explicatives pour l'entraînement d'un modèle.

    - Remplace les NaN par 'inconnu' (catégorielles) ou médiane (numériques)
    - Encode les variables catégorielles avec pd.factorize
    - Retourne un DataFrame nettoyé et encodé

    Paramètres :
    -----------
    df : pd.DataFrame
        DataFrame complet.

    variables_explicatives : List[str]
        Colonnes à utiliser comme variables explicatives.

    verbose : bool, optionnel (default=True)
        Si True, affiche la correspondance code → catégorie pour les colonnes catégorielles.

    Retour :
    -------
    pd.DataFrame
        DataFrame nettoyé et encodé.
    """
    df_clean = df[variables_explicatives].copy()

    for col in df_clean.columns:
        if df_clean[col].dtype == 'object' or df_clean[col].dtype.name == 'category':
            # Remplacement des NaN par 'inconnu' pour les variables catégorielles
            df_clean[col] = df_clean[col].fillna('inconnu').astype(str)

            # Encodage en entiers uniques avec pd.factorize
            codes, uniques = pd.factorize(df_clean[col])
            df_clean[col] = codes

            # Affichage de la correspondance si verbose=True
            if verbose:
                print(f"\nCorrespondance '{col}' :")
                for i, val in enumerate(uniques):
                    print(f"    {i} : {val}")

        else:
            # Remplacement des NaN numériques par la médiane
            if df_clean[col].isnull().sum() > 0:
                median_val = df_clean[col].median()
                df_clean[col] = df_clean[col].fillna(median_val)
                if verbose:
                    print(f"Colonne numérique '{col}': NaN remplacés par la médiane = {median_val}")

    return df_clean


def preparer_pipeline(
    df: pd.DataFrame,
    variables_explicatives: List[str],
    verbose: bool = True
) -> Pipeline:
    """
    Crée un pipeline sklearn complet pour traitement des variables explicatives.

    - Imputation des NaN
    - Encodage des catégorielles
    - Scaling des numériques

    Paramètres :
    -----------
    df : pd.DataFrame
        DataFrame contenant les données.

    variables_explicatives : List[str]
        Colonnes à utiliser comme variables explicatives.

    verbose : bool, optionnel (default=True)
        Si True, affiche les colonnes numériques et catégorielles détectées.

    Retour :
    -------
    sklearn.pipeline.Pipeline
        Pipeline de prétraitement.
    """
    # Identifier colonnes numériques et catégorielles
    colonnes_num = df[variables_explicatives].select_dtypes(include=['int64', 'float64']).columns.tolist()
    colonnes_cat = df[variables_explicatives].select_dtypes(include=['object', 'category']).columns.tolist()

    if verbose:
        logging.info("Variables numériques détectées : %s", colonnes_num)
        logging.info("Variables catégorielles détectées : %s", colonnes_cat)

    # Pipeline pour colonnes numériques
    pipeline_num = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])

    # Pipeline pour colonnes catégorielles
    pipeline_cat = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='constant', fill_value='inconnu')),
        ('encoder', OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1))
    ])

    # Combine les 2 pipelines dans un ColumnTransformer
    preprocessor = ColumnTransformer(transformers=[
        ('num', pipeline_num, colonnes_num),
        ('cat', pipeline_cat, colonnes_cat)
    ])

    return preprocessor


def entrainer_modele(
    df: pd.DataFrame,
    colonne_cible: str,
    variables_explicatives: Optional[List[str]] = None,
    test_size: float = 0.2,
    random_state: int = 42
) -> RandomForestClassifier:
    """
    Entraîne un modèle RandomForestClassifier et affiche les performances.

    Paramètres :
    -----------
    df : pd.DataFrame
        DataFrame complet.

    colonne_cible : str
        Colonne cible à prédire.

    variables_explicatives : List[str], optionnel
        Colonnes à utiliser comme features. Si None, toutes sauf la cible.

    test_size : float, optionnel
        Proportion du test set.

    random_state : int, optionnel
        Graine pour reproductibilité.

    Retour :
    -------
    RandomForestClassifier
        Modèle entraîné.
    """
    X, y = recuperer_entrees_et_cible(df, colonne_cible, variables_explicatives)
    X_clean = preparer_variables_explicatives(X, X.columns.tolist())

    X_train, X_test, y_train, y_test = train_test_split(
        X_clean, y, test_size=test_size, random_state=random_state
    )

    clf = RandomForestClassifier(n_estimators=100, random_state=random_state)
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    logging.info("=== Rapport de classification ===\n%s", classification_report(y_test, y_pred))
    logging.info("=== Matrice de confusion ===\n%s", confusion_matrix(y_test, y_pred))

    return clf


def entrainer_modele_prod(
    df: pd.DataFrame,
    colonne_cible: str,
    variables_explicatives: Optional[List[str]] = None,
    test_size: float = 0.2,
    random_state: int = 42,
    path_model: Optional[str] = None
) -> Tuple[Pipeline, pd.DataFrame, pd.Series]:
    """
    Entraîne un pipeline RandomForest complet et le sauvegarde éventuellement.

    Paramètres :
    -----------
    df : pd.DataFrame
        DataFrame contenant les données.

    colonne_cible : str
        Colonne cible.

    variables_explicatives : List[str], optionnel
        Colonnes features. Si None, toutes sauf la cible.

    test_size : float, optionnel
        Proportion du test set.

    random_state : int, optionnel
        Graine.

    path_model : str, optionnel
        Chemin pour sauvegarder le modèle joblib.

    Retour :
    -------
    Tuple[Pipeline, pd.DataFrame, pd.Series]
        - Pipeline entraîné
        - X_test
        - y_test
    """
    assert colonne_cible in df.columns, f"Colonne cible '{colonne_cible}' introuvable."

    if variables_explicatives is None:
        variables_explicatives = df.drop(columns=[colonne_cible]).columns.tolist()

    X = df[variables_explicatives]
    y = df[colonne_cible]

    preprocessor = preparer_pipeline(df, variables_explicatives)

    model_pipeline = Pipeline(steps=[
        ('preprocessing', preprocessor),
        ('classifier', RandomForestClassifier(n_estimators=100, random_state=random_state))
    ])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    logging.info("Taille train : %d", len(y_train))
    logging.info("Taille test : %d", len(y_test))

    model_pipeline.fit(X_train, y_train)

    y_pred = model_pipeline.predict(X_test)
    logging.info("=== Rapport de classification ===\n%s", classification_report(y_test, y_pred))
    logging.info("=== Matrice de confusion ===\n%s", confusion_matrix(y_test, y_pred))

    if path_model is not None:
        joblib.dump(model_pipeline, path_model)
        logging.info("Modèle sauvegardé sous : %s", path_model)

    return model_pipeline, X_test, y_test
