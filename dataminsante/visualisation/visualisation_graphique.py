# -*- coding: utf-8 -*-

# dataminsante/visualisation_graphique.py
import logging
import re
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
import pandas as pd
from typing import Optional, Union, List, Tuple, Dict
from pandas.api.types import is_numeric_dtype

# Configure le logger au début du module
logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')


# --- Fonction utilitaire ---

def verifier_presence_colonnes(df: pd.DataFrame, colonnes: Union[str, List[str], str]) -> bool:
    """
    Vérifie que les colonnes spécifiées existent dans le DataFrame.

    Args:
        df (pd.DataFrame): Le DataFrame à vérifier.
        colonnes (Union[str, List[str], *str]): Une ou plusieurs colonnes à vérifier.

    Returns:
        bool: True si toutes les colonnes sont présentes, sinon False.
    """
    # Gérer plusieurs colonnes en *args ou en liste
    if isinstance(colonnes, tuple):
        colonnes = list(colonnes)
    elif isinstance(colonnes, str):
        colonnes = [colonnes]
    elif isinstance(colonnes, list):
        pass
    else:
        logger.error(f"[ERREUR] Format non supporté pour les colonnes : {type(colonnes)}")
        return False

    for col in colonnes:
        if col not in df.columns:
            logger.error(f"[ERREUR] Colonne '{col}' non trouvée dans le DataFrame.")
            return False
    return True

def compter_par_categorie(
    df: pd.DataFrame,
    colonne: str,
    seuil_min: int = 0
) -> pd.DataFrame:
    """
    Compte les occurrences d'une colonne catégorielle et filtre les catégories
    dont le nombre d'occurrences est inférieur au seuil_min.

    Args:
        df (pd.DataFrame): DataFrame source.
        colonne (str): Nom de la colonne catégorielle à analyser.
        seuil_min (int, optional): Seuil minimal d'occurrences pour conserver la catégorie.
                                   Par défaut 0 (toutes les catégories).

    Returns:
        pd.DataFrame: DataFrame avec colonnes [colonne, 'Nombre de cas'] filtrée.

    Raises:
        ValueError: Si la colonne n'existe pas dans le DataFrame.
    """
    if colonne not in df.columns:
        raise ValueError(f"[ERREUR] Colonne '{colonne}' non trouvée dans le DataFrame.")
    counts = df[colonne].value_counts()
    filtered = counts[counts >= seuil_min].reset_index()
    filtered.columns = [colonne, 'Nombre de cas']
    return filtered


# Histogramme et barres

## Graphiques en barres
def plot_bar_par_categorie_plotly(
    df: pd.DataFrame,
    col_categorie: str,
    titre: Optional[str] = None,
    seuil_min: int = 0,
    annot: bool = False,
    rotation: int = 0
) -> Optional[go.Figure]:
    """
    Affiche un graphique en barres Plotly Express des occurrences par catégorie,
    avec filtrage selon un seuil minimal.

    Args:
        df (pd.DataFrame): DataFrame source.
        col_categorie (str): Colonne catégorielle pour l'axe X.
        titre (str, optional): Titre du graphique.
        seuil_min (int, optional): Seuil minimal d'occurrences à afficher.
        annot (bool, optional): Affiche les annotations (valeurs) sur les barres si True.
        rotation (int, optional): Angle de rotation des labels de l'axe X (en degrés).

    Returns:
        plotly.graph_objs._figure.Figure ou None
    """
    try:
        df_grouped = compter_par_categorie(df, col_categorie, seuil_min)
    except ValueError as e:
        logger.error(e)
        return None

    if df_grouped.empty:
        logger.info("[INFO] Aucune catégorie ne correspond au seuil minimal.")
        return None

    params_px_bar = dict(
        data_frame=df_grouped,
        x=col_categorie,
        y='Nombre de cas',
        title=titre or f"Nombre de cas par {col_categorie}",
        color=col_categorie,
        color_discrete_sequence=px.colors.qualitative.Plotly
    )
    if annot:
        params_px_bar['text'] = 'Nombre de cas'

    fig = px.bar(**params_px_bar)
    fig.update_layout(xaxis_title=col_categorie, yaxis_title='Nombre de cas')

    if annot:
        fig.update_traces(textposition='outside', texttemplate='%{text}')

    if rotation != 0:
        fig.update_layout(xaxis_tickangle=-rotation)

    fig.show()

## Graphiques en barres groupées interactifs
def plot_bar_grouped_interactif(
    df: pd.DataFrame,
    colonnes: Union[str, List[str], Tuple[str, ...]],
    seuil_min: int = 0,
    titre: Optional[str] = None,
    rotation: int = 45,
    annot: bool = False,
    bargap: float = 0.2,
    bargroupgap: float = 0.1
) -> Optional[go.Figure]:
    """
    Affiche un graphique en barres groupées interactif pour 1 ou 2 colonnes catégorielles avec Plotly Express.

    Args:
        df (pd.DataFrame): DataFrame source.
        colonnes (str | list | tuple): Colonnes de regroupement (1 ou 2 maximum).
        seuil_min (int, optional): Seuil minimal d’occurrences à afficher.
        titre (str, optional): Titre du graphique.
        rotation (int, optional): Rotation des labels axe X.
        annot (bool, optional): Affiche les annotations des valeurs.
        bargap (float, optional): Espace entre les groupes de barres (0 = collés, 1 = très espacés).
        bargroupgap (float, optional): Espace entre les barres dans un même groupe.

    Returns:
        plotly.graph_objs._figure.Figure ou None
    """
    if isinstance(colonnes, str):
        colonnes = [colonnes]

    if not verifier_presence_colonnes(df, colonnes):
        return None

    # Calcul des fréquences
    counts = df.groupby(colonnes).size().reset_index(name='Nombre de cas')
    filtered = counts[counts['Nombre de cas'] >= seuil_min].reset_index(drop=True)

    # Construction du graphique
    if len(colonnes) == 1:
        fig = px.bar(
            filtered,
            x=colonnes[0],
            y='Nombre de cas',
            color=colonnes[0],
            title=titre or f"Nombre de cas par {colonnes[0]}",
            labels={colonnes[0]: colonnes[0], 'Nombre de cas': 'Nombre de cas'}
        )
    elif len(colonnes) == 2:
        fig = px.bar(
            filtered,
            x=colonnes[0],
            y='Nombre de cas',
            color=colonnes[1],
            barmode='group',
            title=titre or f"Nombre de cas par {colonnes[0]} et {colonnes[1]}",
            labels={
                colonnes[0]: colonnes[0],
                colonnes[1]: colonnes[1],
                'Nombre de cas': 'Nombre de cas'
            }
        )
    else:
        raise NotImplementedError("Le graphique supporte au maximum 2 colonnes pour le groupement.")

    # Mise en forme
    fig.update_layout(
        xaxis_tickangle=-rotation,
        bargap=bargap,
        bargroupgap=bargroupgap,
        template='plotly_white'
    )

    # Affichage des annotations
    if annot:
        fig.update_traces(texttemplate='%{y}', textposition='auto')

    fig.show()

## Graphiques en histogramme
def plot_histogramme_par_categorie_plotly(
    df: pd.DataFrame,
    colonne: str,
    titre: Optional[str] = None,
    seuil_min: int = 0,
    annot: bool = False,
    rotation: int = 45,
    taille_fig: Optional[Tuple[int, int]] = None  # Ajout du paramètre
) -> Optional[go.Figure]:
    """
    Affiche un histogramme (bar chart) des occurrences pour une colonne catégorielle,
    avec options d'affichage des valeurs au-dessus des barres et rotation des labels X.

    Args:
        df (pd.DataFrame): DataFrame source.
        colonne (str): Colonne catégorielle à analyser.
        titre (str, optional): Titre du graphique.
        seuil_min (int, optional): Seuil minimal d'occurrences à afficher.
        annot (bool, optional): Affiche les valeurs sur les barres si True.
        rotation (int, optional): Angle de rotation des labels de l'axe X (en degrés).
        taille_fig (Tuple[int, int], optional): Taille du graphique (largeur, hauteur).

    Returns:
        plotly.graph_objs._figure.Figure ou None
    """
    try:
        df_grouped = compter_par_categorie(df, colonne, seuil_min)
    except ValueError as e:
        logger.error(e)
        return None

    if df_grouped.empty:
        logger.info("[INFO] Aucune catégorie ne correspond au seuil minimal.")
        return None

    params_px_bar = dict(
        data_frame=df_grouped,
        x=colonne,
        y='Nombre de cas',
        title=titre or f"Histogramme du nombre de cas par '{colonne}'",
        labels={colonne: colonne, 'Nombre de cas': 'Nombre de cas'},
        color=colonne,
        color_discrete_sequence=px.colors.qualitative.Plotly
    )
    if annot:
        params_px_bar['text'] = 'Nombre de cas'

    fig = px.bar(**params_px_bar)

    if annot:
        fig.update_traces(textposition='outside', texttemplate='%{text}')
    else:
        fig.update_traces(textposition=None)

    fig.update_layout(xaxis_tickangle=-rotation)

    if taille_fig:
        fig.update_layout(width=taille_fig[0], height=taille_fig[1])

    fig.show()

## Graphiques en histogramme groupé
def plot_histogramme_groupe(
    df: pd.DataFrame,
    x_col: str,
    x_titre: str,
    hue_col: str,
    y_titre: str = "Nombre de cas",
    titre: Optional[str] = None,
    rotation: int = 45,
    annot: bool = False
) -> Optional[plt.Axes]:
    """
    📊 Affiche un histogramme groupé avec Seaborn countplot.

    Args:
        df (pd.DataFrame): DataFrame source.
        x_col (str): Colonne en abscisse.
        x_titre (str): Titre de l’axe X.
        hue_col (str): Colonne pour la couleur/groupement.
        y_titre (str): Titre de l’axe Y.
        titre (str, optional): Titre du graphique.
        rotation (int, optional): Rotation des labels axe X.
        annot (bool, optional): Affiche les annotations des valeurs.

    Returns:
        matplotlib.axes._subplots.AxesSubplot ou None
    """
    if not verifier_presence_colonnes(df, [x_col, hue_col]):
        return None

    # 📐 Taille de la figure
    plt.figure(figsize=(12, 6))
    ax = sns.countplot(data=df, x=x_col, hue=hue_col)

    # 🎯 Titres et étiquettes
    plt.title(titre or f"Répartition de '{x_col}' par '{hue_col}'")
    plt.xlabel(x_titre)
    plt.ylabel(y_titre)
    plt.xticks(rotation=rotation)

    # 📊 Grille horizontale
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()

    # 🏷️ Annotations si demandé
    if annot:
        for p in ax.patches:
            hauteur = p.get_height()
            if hauteur > 0:
                ax.annotate(
                    f'{int(hauteur)}',
                    (p.get_x() + p.get_width() / 2., hauteur),
                    ha='center',
                    va='bottom',
                    fontsize=9,
                    xytext=(0, 3),
                    textcoords='offset points'
                )

    plt.show()

## Graphiques en histogramme groupé interactif
def plot_histogramme_groupe_interactif(
    df: pd.DataFrame,
    x_col: str,
    x_titre: str,
    hue_col: str,
    y_titre: str = "Nombre de cas",
    titre: Optional[str] = None,
    rotation: int = 45,
    annot: bool = False,
    pas_x: Optional[int] = None,
    bargap: float = 0.2,         # Espace entre groupes
    bargroupgap: float = 0.1,    # Espace entre barres d'un même groupe
    taille_fig: Tuple[int, int] = (1500, 500)  # Largeur, hauteur
) -> Optional[go.Figure]:
    """
    📊 Affiche un histogramme groupé interactif avec Plotly Express.

    Args:
        df (pd.DataFrame): DataFrame source.
        x_col (str): Colonne en abscisse.
        x_titre (str): Titre de l’axe X.
        hue_col (str): Colonne de regroupement.
        y_titre (str): Titre de l’axe Y.
        titre (str, optional): Titre du graphique.
        rotation (int, optional): Rotation des labels axe X.
        annot (bool, optional): Affiche les annotations des valeurs.
        pas_x (int, optional): Intervalle d’affichage des ticks sur l’axe X.
        bargap (float, optional): Espace entre groupes de barres (0 à 1).
        bargroupgap (float, optional): Espace entre barres d’un même groupe (0 à 1).
        taille_fig (Tuple[int, int], optional): Dimensions (largeur, hauteur) du graphique.

    Returns:
        plotly.graph_objs._figure.Figure ou None
    """
    if not verifier_presence_colonnes(df, [x_col, hue_col]):
        return None

    # 🔍 Tri alphanumérique des catégories X
    def extraire_numero(x):
        match = re.search(r'\d+', str(x))
        return int(match.group()) if match else -1

    categories_x = sorted(df[x_col].dropna().unique(), key=extraire_numero)

    # 📊 Création de l'histogramme
    fig = px.histogram(
        df,
        x=x_col,
        color=hue_col,
        barmode='group',
        title=titre or f"Répartition de '{x_col}' par '{hue_col}'",
        labels={x_col: x_titre, hue_col: hue_col},
        category_orders={x_col: categories_x}
    )

    # 🎨 Mise en forme du graphique
    fig.update_layout(
        xaxis_title=x_titre,
        yaxis_title=y_titre,
        bargap=bargap,
        bargroupgap=bargroupgap,
        template='plotly_white',
        xaxis_tickangle=-rotation,
        width=taille_fig[0],
        height=taille_fig[1]
    )

    # 🏷️ Annotations si demandé
    if annot:
        fig.update_traces(texttemplate='%{y}', textposition='outside')

    # 📏 Gestion des ticks de l'axe X
    if pas_x is not None:
        try:
            tickvals = [categories_x[i] for i in range(0, len(categories_x), pas_x)]
            fig.update_xaxes(tickmode='array', tickvals=tickvals, ticktext=tickvals)
        except Exception:
            pass

    fig.show()

## Graphiques en histogramme empilé interactif
def plot_histogramme_groupe_interactif_empile(
    df: pd.DataFrame,
    x_col: str,
    x_titre: str,
    hue_col: str,
    y_titre: str = "Nombre de cas",
    titre: Optional[str] = None,
    rotation: int = 45,
    annot: bool = False,
    pas_x: Optional[int] = None,
    bargap: float = 0.2,
    bargroupgap: float = 0.1,
    taille_fig: Tuple[int, int] = (1500, 500),
    x_trier: bool = False,
    ordre: str = "asc"
) -> Optional[go.Figure]:
    """
    📊 Affiche un histogramme empilé interactif avec Plotly.

    Cette fonction permet deux modes :
    1️⃣ Mode standard Plotly Express (x_trier=False) : affichage simple empilé.
    2️⃣ Mode tri des segments (x_trier=True) : les segments (hue_col) 
       sont triés du plus petit au plus grand ou inversement dans chaque barre.

    Args:
        df (pd.DataFrame): DataFrame source.
        x_col (str): Nom de la colonne à placer sur l'axe X.
        x_titre (str): Titre à afficher pour l'axe X.
        hue_col (str): Colonne de regroupement (empilement des segments).
        y_titre (str, optional): Titre de l'axe Y (par défaut "Nombre de cas").
        titre (str, optional): Titre du graphique.
        rotation (int, optional): Angle de rotation des labels de l'axe X.
        annot (bool, optional): Affiche les valeurs sur chaque segment.
        pas_x (int, optional): Intervalle d'affichage des ticks de l'axe X.
        bargap (float, optional): Espacement entre groupes de barres (0 à 1).
        bargroupgap (float, optional): Espacement entre barres d'un même groupe (0 à 1).
        taille_fig (Tuple[int, int], optional): Dimensions du graphique (largeur, hauteur).
        x_trier (bool, optional): Si True, trie les segments dans chaque barre.
        ordre (str, optional): "asc" pour tri croissant, "desc" pour tri décroissant.

    Returns:
        go.Figure ou None: Objet figure Plotly affichable ou None si erreur.
    """

    if not all(col in df.columns for col in [x_col, hue_col]):
        print("❌ Colonnes manquantes dans le DataFrame")
        return None

    # Tri naturel de l'axe X
    def extraire_numero(x):
        match = re.search(r'\d+', str(x))
        return int(match.group()) if match else -1

    categories_x = sorted(df[x_col].dropna().unique(), key=extraire_numero)

    if not x_trier:
        # Mode simple avec Plotly Express
        fig = px.histogram(
            df,
            x=x_col,
            color=hue_col,
            barmode='stack',
            title=titre or f"Histogramme empilé de '{x_col}' par '{hue_col}'",
            labels={x_col: x_titre, hue_col: hue_col},
            category_orders={x_col: categories_x}
        )
        if annot:
            fig.update_traces(texttemplate='%{y}', textposition='outside')
        fig.update_layout(
            xaxis_title=x_titre,
            yaxis_title=y_titre,
            bargap=bargap,
            bargroupgap=bargroupgap,
            template='plotly_white',
            xaxis_tickangle=-rotation,
            width=taille_fig[0],
            height=taille_fig[1]
        )
        if pas_x is not None:
            tickvals = [categories_x[i] for i in range(0, len(categories_x), pas_x)]
            fig.update_xaxes(tickmode='array', tickvals=tickvals, ticktext=tickvals)

    else:
        # Mode tri des segments
        df_agg = df.groupby([x_col, hue_col]).size().reset_index(name="valeur")
        fig = go.Figure()
        for semaine in categories_x:
            sous_df = df_agg[df_agg[x_col] == semaine].copy()
            ascending = True if ordre == "asc" else False
            sous_df = sous_df.sort_values("valeur", ascending=ascending)
            cumul = 0
            for _, row in sous_df.iterrows():
                fig.add_trace(go.Bar(
                    x=[semaine],
                    y=[row["valeur"]],
                    name=row[hue_col],
                    offsetgroup=str(semaine),
                    base=cumul,
                    text=[row["valeur"]] if annot else None,
                    textposition="inside" if annot else "none",
                    showlegend=bool(semaine == categories_x[0])
                ))
                cumul += row["valeur"]
        fig.update_layout(
            barmode="stack",
            bargap=bargap,
            bargroupgap=bargroupgap,
            xaxis_title=x_titre,
            yaxis_title=y_titre,
            title=titre,
            template="plotly_white",
            width=taille_fig[0],
            height=taille_fig[1],
            xaxis_tickangle=-rotation
        )
        if pas_x is not None:
            tickvals = [categories_x[i] for i in range(0, len(categories_x), pas_x)]
            fig.update_xaxes(tickmode='array', tickvals=tickvals, ticktext=tickvals)

    fig.show()

## Graphiques à barres avec facettes
def graphique_barres_facette(
    df: pd.DataFrame,
    x_col: str = "Num_semaine_epi",
    x_titre: str = "Semaine épidémiologique",
    y_col: str = "Cases",
    y_titre: str = "Nombre de cas",
    facette_col: str = "Province",
    titre: Optional[str] = "Répartition des cas",
    taille_fig: Tuple[int, int] = (1600, 600),
    rotation: int = 45,
    couleurs_personnalisees: Optional[Union[str, dict]] = None,
    bargap: float = 0.2,
    bargroupgap: float = 0.1,
    annot: bool = False,
    pas_x: Optional[int] = None,
    auto_aggregate: bool = True,
    filtre_valeur: Optional[str] = None,
    return_fig: bool = False,
    encadrer_facettes: bool = True,            # activer/désactiver cadre
    couleur_contour_facette: str = "#E6E6DD"      #  Couleur du cadre
):
    """
    Affiche un histogramme facetté ou groupé avec option d’encadrement des facettes.

    ...

    Paramètres :
    - encadrer_facettes (bool) : afficher un contour autour de chaque facette (défaut False)
    - couleur_contour_facette (str) : couleur du contour (par défaut "black")
    """

    df = df.copy()

    # Filtre si demandé
    if filtre_valeur is not None:
        df = df[df[facette_col] == filtre_valeur]
        facet_col = None
    else:
        facet_col = facette_col

    # Comptage ou agrégation
    if not is_numeric_dtype(df[y_col]):
        df = df.groupby([facette_col, x_col]).size().reset_index(name="Nb_occurrences")
        y_col = "Nb_occurrences"
        y_titre = "Nombre d’occurrences"
    elif auto_aggregate:
        df = df.groupby([facette_col, x_col])[y_col].sum().reset_index()

    # Tri des facettes
    categories = sorted(df[facette_col].dropna().unique())
    df[facette_col] = pd.Categorical(df[facette_col], categories=categories, ordered=True)

    # Couleurs personnalisées
    if isinstance(couleurs_personnalisees, dict):
        color_map = couleurs_personnalisees
        color_col = facette_col
    elif isinstance(couleurs_personnalisees, str):
        df["Couleur_unique"] = "Unique"
        color_col = "Couleur_unique"
        color_map = {"Unique": couleurs_personnalisees}
    else:
        color_col = facette_col if facet_col is not None else None
        color_map = None

    # Création du graphique
    fig = px.bar(
        df,
        x=x_col,
        y=y_col,
        color=color_col,
        facet_col=facet_col,
        facet_col_wrap=4 if facet_col is not None else None,
        color_discrete_map=color_map,
        labels={x_col: "", y_col: "", facette_col: facette_col},
        title=titre,
        height=taille_fig[1],
        width=taille_fig[0],
    )

    # Mise en forme
    fig.update_layout(
        template="plotly_white",
        showlegend=False,
        bargap=bargap,
        bargroupgap=bargroupgap,
        xaxis_tickangle=rotation,
        title_x=0.5,
        margin=dict(t=80, b=80, l=80)
    )

    # Espacement X si demandé
    if pas_x is not None:
        fig.update_xaxes(tickmode='linear', dtick=pas_x)

    # Nettoyer titres facettes
    if facet_col is not None:
        fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))

    # Supprimer titres par facette
    fig.update_xaxes(title_text="")
    fig.update_yaxes(title_text="")

    # Titres globaux
    fig.add_annotation(
        x=0.5, y=-0.12, xref='paper', yref='paper',
        showarrow=False,
        text=x_titre,
        font=dict(size=14),
        xanchor='center',
        yanchor='top'
    )
    fig.add_annotation(
        x=-0.07, y=0.5, xref='paper', yref='paper',
        showarrow=False,
        text=y_titre,
        font=dict(size=14),
        textangle=-90,
        xanchor='center',
        yanchor='middle'
    )

    # Annotations valeurs si demandé
    if annot:
        fig.update_traces(texttemplate='%{y}', textposition='outside', cliponaxis=False)

    # 📦 Encadrer chaque facette par un contour coloré si demandé
    if encadrer_facettes:
        for axis in fig.layout:
            if isinstance(fig.layout[axis], go.layout.XAxis) and "domain" in fig.layout[axis]:
                yaxis_name = axis.replace("xaxis", "yaxis")
                if yaxis_name in fig.layout and "domain" in fig.layout[yaxis_name]:
                    x0, x1 = fig.layout[axis].domain
                    y0, y1 = fig.layout[yaxis_name].domain
                    fig.add_shape(
                        type="rect",
                        x0=x0, x1=x1,
                        y0=y0, y1=y1,
                        xref="paper", yref="paper",
                        line=dict(color=couleur_contour_facette, width=1),
                        fillcolor="rgba(0,0,0,0)"
                    )

    if return_fig:
        return fig
    else:
        fig.show()

# Courbe
## Graphiques en courbe
def plot_courbe_plotly(
    df: pd.DataFrame,
    colonne: str,
    titre: Optional[str] = None,
    annot: bool = False,
    rotation: int = 0,
    marker_size: int = 8,
    pas_x: Optional[int] = None,
    taille_fig: Tuple[int, int] = (1500, 500)  
) -> Optional[go.Figure]:
    """
    Affiche une courbe du nombre de cas par catégorie avec Plotly Express,
    avec options d'annotations sur les points, rotation des labels X et taille personnalisée.

    Args:
        df (pd.DataFrame): DataFrame source.
        colonne (str): Colonne à analyser.
        titre (str, optional): Titre du graphique.
        annot (bool, optional): Affiche les valeurs sur les points si True.
        rotation (int, optional): Angle de rotation des labels de l'axe X (en degrés).
        marker_size (int, optional): Taille des marqueurs.
        pas_x (int, optional): Intervalle entre les ticks de l'axe X.
        taille_fig (Tuple[int, int], optional): Dimensions (largeur, hauteur) du graphique.

    Returns:
        plotly.graph_objs._figure.Figure ou None
    """
    if not verifier_presence_colonnes(df, colonne):
        return None

    cas = df.groupby(colonne).size().reset_index(name='Nombre de cas')

    # Tri alphanumérique basé sur les parties numériques de la chaîne
    def extraire_numero(x):
        match = re.search(r'\d+', str(x))
        return int(match.group()) if match else -1

    categories_x = sorted(cas[colonne].dropna().unique(), key=extraire_numero)
    cas[colonne] = pd.Categorical(cas[colonne], categories=categories_x, ordered=True)

    # Création de la courbe
    params_px_line = dict(
        data_frame=cas,
        x=colonne,
        y='Nombre de cas',
        title=titre or f"Courbe par '{colonne}'",
        markers=True,
        labels={colonne: colonne, 'Nombre de cas': 'Nombre de cas'},
        color_discrete_sequence=['blue']
    )
    fig = px.line(**params_px_line)

    # Annotations si demandé
    if annot:
        fig.add_trace(go.Scatter(
            x=cas[colonne],
            y=cas['Nombre de cas'],
            mode='text',
            text=cas['Nombre de cas'],
            textposition='top center',
            showlegend=False
        ))

    # Rotation des labels X
    if rotation != 0:
        fig.update_layout(xaxis_tickangle=-rotation)

    # Taille des marqueurs
    fig.update_traces(marker=dict(size=marker_size))

    # Taille du graphique
    fig.update_layout(width=taille_fig[0], height=taille_fig[1])

    # Ticks personnalisés
    if pas_x is not None:
        try:
            tickvals = [categories_x[i] for i in range(0, len(categories_x), pas_x)]
            fig.update_xaxes(tickmode='array', tickvals=tickvals, ticktext=tickvals)
        except Exception:
            pass

    fig.show()

## Graphiques en courbe par catégories interactifs
def plot_courbe_par_categories_plotly(
    df: pd.DataFrame,
    colonne_x: str,
    colonne_y: str,
    titre: Optional[str] = None,
    rotation: int = 45,
    annot: bool = False,
    pas_x: Optional[int] = None,
    taille_fig: Tuple[int, int] = (700, 500) 
) -> Optional[go.Figure]:
    """
    Trace une ou plusieurs courbes du nombre de cas par catégorie avec Plotly Express.

    Args:
        df (pd.DataFrame): Données sources.
        colonne_x (str): Variable pour l'axe des X (ex: semaine).
        colonne_y (str): Variable pour les groupes/séries (ex: province).
        titre (str, optional): Titre du graphique.
        rotation (int, optional): Rotation des labels de l'axe X.
        annot (bool, optional): Ajoute les valeurs sur les points.
        pas_x (int, optional): Intervalle entre les ticks X.
        taille_fig (Tuple[int, int], optional): Dimensions (largeur, hauteur) du graphique.

    Returns:
        plotly.graph_objs._figure.Figure ou None
    """
    if not verifier_presence_colonnes(df, [colonne_x, colonne_y]):
        logger.info("Colonnes manquantes")
        return None

    # Regroupement des données
    cas = df.groupby([colonne_x, colonne_y], observed=True).size().reset_index(name='Nombre de cas')

    # Tri alphanumérique
    def extraire_numero(x):
        match = re.search(r'\d+', str(x))
        return int(match.group()) if match else -1

    ordre_x = sorted(cas[colonne_x].unique(), key=extraire_numero)
    cas[colonne_x] = pd.Categorical(cas[colonne_x], categories=ordre_x, ordered=True)

    # Paramètres pour px.line
    fig_args = {
        'data_frame': cas,
        'x': colonne_x,
        'y': 'Nombre de cas',
        'color': colonne_y,
        'markers': True,
        'title': titre or f"Courbe de 'Nombre de cas' par '{colonne_x}' et '{colonne_y}'",
        'labels': {
            colonne_x: colonne_x,
            'Nombre de cas': 'Nombre de cas',
            colonne_y: colonne_y
        },
        'category_orders': {colonne_x: ordre_x},
        'color_discrete_sequence': px.colors.qualitative.Set1
    }

    if annot:
        fig_args['text'] = 'Nombre de cas'

    fig = px.line(**fig_args)

    fig.update_layout(
        xaxis_tickangle=-rotation,
        template='plotly_white',
        xaxis_title=colonne_x,
        yaxis_title='Nombre de cas',
        width=taille_fig[0],  # 📌 Largeur
        height=taille_fig[1]  # 📌 Hauteur
    )

    if annot:
        fig.update_traces(textposition='top center')

    if pas_x is not None:
        try:
            tickvals = [ordre_x[i] for i in range(0, len(ordre_x), pas_x)]
            fig.update_xaxes(tickmode='array', tickvals=tickvals, ticktext=tickvals)
        except Exception as e:
            logger.info(f"Erreur lors de la génération des ticks personnalisés : {e}")

    fig.show()


# Camembert
## Graphiques en camembert (donut)
def plot_camembert_par_categorie(
    df: pd.DataFrame,
    colonne: str,
    titre: Optional[str] = None,
    seuil_min: int = 0,
    afficher_legende: bool = True,
    annot: bool = True,
    figsize: Tuple[int, int] = (10, 6)
) -> Optional[plt.Axes]:
    """
    Affiche un diagramme circulaire (camembert) avec un style "donut".

    Args:
        df (pd.DataFrame): DataFrame source.
        colonne (str): Colonne catégorielle à analyser.
        titre (str, optional): Titre du graphique.
        seuil_min (int, optional): Seuil minimal d'occurrences à afficher.
        afficher_legende (bool, optional): Affiche la légende à droite.
        annot (bool, optional): Affiche les pourcentages sur le camembert si True.
        figsize (tuple, optional): Taille de la figure matplotlib.

    Returns:
        matplotlib.axes._subplots.AxesSubplot ou None
    """
    if not verifier_presence_colonnes(df, colonne):
        return None

    cas = df[colonne].value_counts()
    cas = cas[cas >= seuil_min]

    if cas.empty:
        logger.info("[INFO] Aucune catégorie ne correspond au seuil minimal.")
        return None

    labels = cas.index
    tailles = cas.values

    plt.figure(figsize=figsize)
    autopct_val = '%1.1f%%' if annot else None
    patches, texts, autotexts = plt.pie(
        tailles,
        labels=labels,
        autopct=autopct_val,
        startangle=140,
        pctdistance=0.85,
        wedgeprops=dict(width=0.4, edgecolor='w')
    )
    plt.title(titre or f"Répartition des cas par '{colonne}'")
    plt.axis('equal')
    plt.tight_layout()

    if afficher_legende:
        plt.legend(patches, labels, loc='center left', bbox_to_anchor=(1, 0.5))

    plt.show()

## Graphiques en camembert interactif
def plot_camembert_interactif(
    df: pd.DataFrame,
    colonne: Union[str, List[str]],
    titre: Optional[str] = None,
    seuil_min: int = 0,
    afficher_legende: bool = True,
    annot: bool = True,
    taille_fig: Tuple[int, int] = (700, 500),
    palette_couleurs: Optional[List[str]] = None 
) -> Optional[go.Figure]:
    """
    Affiche un diagramme circulaire (donut) interactif avec Plotly.
    Accepte une colonne ou une liste de colonnes (elles seront concaténées).

    Args:
        df (pd.DataFrame): DataFrame source.
        colonne (str or list): Colonne ou liste de colonnes à analyser.
        titre (str, optional): Titre du graphique.
        seuil_min (int, optional): Seuil minimal d'occurrences à afficher.
        afficher_legende (bool, optional): Affiche la légende.
        annot (bool, optional): Affiche les pourcentages sur les parts.
        taille_fig (tuple, optional): Taille de la figure (largeur, hauteur).
        palette_couleurs (list, optional): Liste de couleurs personnalisées pour le diagramme.

    Returns:
        plotly.graph_objs._figure.Figure ou None
    """
    # Vérification colonne(s)
    if isinstance(colonne, list):
        for col in colonne:
            if col not in df.columns:
                print(f"[ERREUR] Colonne '{col}' absente du DataFrame")
                return None
        nom_col_temp = "_colonne_concat_"
        df[nom_col_temp] = df[colonne].astype(str).agg(" - ".join, axis=1)
        colonne_effective = nom_col_temp
    else:
        if colonne not in df.columns:
            print(f"[ERREUR] Colonne '{colonne}' absente du DataFrame")
            return None
        colonne_effective = colonne

    # Comptage des valeurs et filtre par seuil_min
    counts = df[colonne_effective].value_counts()
    counts = counts[counts >= seuil_min]

    if counts.empty:
        print("[INFO] Aucune catégorie ne correspond au seuil minimal.")
        return None

    labels = counts.index.tolist()
    valeurs = counts.values.tolist()

    # Si une palette de couleurs est fournie, l'appliquer
    if palette_couleurs:
        colors = palette_couleurs
    else:
        colors = None  # Utilise la palette par défaut si aucune n'est donnée

    # Création du graphique
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=valeurs,
        hole=0.4,
        textinfo='percent+label' if annot else 'label',
        hoverinfo='label+value+percent',
        marker=dict(line=dict(color='#FFFFFF', width=2), colors=colors)
    )])

    # Mise à jour du layout
    fig.update_layout(
        title=titre or f"Répartition des cas par {colonne if isinstance(colonne, str) else ', '.join(colonne)}",
        legend=dict(
            orientation="v",
            y=0.5,
            yanchor="middle",
            x=1.05,
            xanchor="left"
        ) if afficher_legende else dict(visible=False),
        width=taille_fig[0],
        height=taille_fig[1],
        margin=dict(l=20, r=150 if afficher_legende else 20, t=40, b=20)
    )

    fig.show()


# Pyramide
## Graphiques en pyramide symétrique
def extraire_ordre_tranche(tranche: str) -> float:
    """
    Retourne un nombre représentant l’ordre logique d’une tranche d’âge.
    Gère les unités "mois", "ans", les bornes "<" et ">" pour un tri cohérent.

    Exemples :
        "0-11 mois"   => 0
        "12-59 mois"  => 12
        "<5 ans"      => 59.5
        "5-15 ans"    => 60
        ">15 ans"     => 1000
    """
    tranche = tranche.lower().strip()

    # Détecter l'unité
    if "mois" in tranche:
        facteur = 1
    elif "semaine" in tranche:
        facteur = 1 / 4  # approximatif
    else:
        facteur = 12  # "ans" ou par défaut

    # Gestion des cas spéciaux < et >
    if tranche.startswith('<'):
        match = re.search(r"(\d+)", tranche)
        if match:
            return int(match.group(1)) * facteur - 0.5
        return 0

    if tranche.startswith('>'):
        match = re.search(r"(\d+)", tranche)
        if match:
            return int(match.group(1)) * facteur + 1000
        return 9999

    # Format "X-Y"
    match = re.match(r"(\d+)[^\d]+(\d+)", tranche)
    if match:
        debut = int(match.group(1))
        return debut * facteur

    # Fallback : un seul chiffre ?
    match = re.search(r"(\d+)", tranche)
    if match:
        return int(match.group(1)) * facteur

    return 9999  # Si non reconnu

def plot_pyramide_symetrique(
    df: pd.DataFrame,
    col_categorie: str,
    col_groupe: str,
    valeurs_neg: Optional[List[str]] = None,
    titre: Optional[str] = "Pyramide Symétrique",
    seuil_min: int = 0,
    afficher_signe_negatif: bool = True,
    afficher_signe_negatif_dans_label: bool = True,
    croissant: bool = True
) -> Optional[go.Figure]:
    """
    Trace un graphique en pyramide symétrique pour comparer deux groupes sur une catégorie ordonnée.

    Args:
        df (pd.DataFrame): Données sources.
        col_categorie (str): Colonne des catégories (axe vertical).
        col_groupe (str): Colonne du groupe qui divise gauche/droite.
        valeurs_neg (list, optional): Valeurs du groupe à inverser (affichées côté négatif).
        titre (str, optional): Titre du graphique.
        seuil_min (int, optional): Seuil minimal de comptage pour filtrer.
        afficher_signe_negatif (bool, optional): Si False, n'applique pas le signe négatif même pour valeurs_neg.
        afficher_signe_negatif_dans_label (bool, optional): Si False, n'affiche pas le signe négatif dans les étiquettes.
        croissant (bool, optional): Ordre des catégories sur l'axe Y (True pour croissant, False pour décroissant).

    Returns:
        plotly.graph_objs._figure.Figure ou None
    """
    if not verifier_presence_colonnes(df, [col_categorie, col_groupe]):
        return None

    counts = df.groupby([col_categorie, col_groupe]).size().reset_index(name='Nombre de cas')
    counts = counts[counts['Nombre de cas'] >= seuil_min]

    if counts.empty:
        logger.info("[INFO] Aucun groupe ne correspond au seuil minimal.")
        return None

    if valeurs_neg is not None and afficher_signe_negatif:
        valeurs_neg_lower = {v.lower() for v in valeurs_neg}
        counts['Nombre de cas'] = counts.apply(
            lambda row: -row['Nombre de cas'] if str(row[col_groupe]).lower() in valeurs_neg_lower else row['Nombre de cas'],
            axis=1
        )

    # Ajouter colonne de texte sans signe négatif si demandé
    if not afficher_signe_negatif_dans_label:
        counts['label_text'] = counts['Nombre de cas'].abs().astype(str)
    else:
        counts['label_text'] = counts['Nombre de cas'].astype(str)

    # Tri logique des catégories
    try:
        ordre_categories = sorted(
            counts[col_categorie].unique(),
            key=extraire_ordre_tranche,
            reverse=not croissant
        )
    except Exception as e:
        logger.warning(f"[WARN] Échec du tri logique: {e}")
        ordre_categories = sorted(counts[col_categorie].unique(), reverse=not croissant)

    counts[col_categorie] = pd.Categorical(counts[col_categorie], categories=ordre_categories, ordered=True)

    fig = px.bar(
        counts,
        y=col_categorie,
        x='Nombre de cas',
        color=col_groupe,
        orientation='h',
        title=titre,
        labels={
            col_categorie: col_categorie,
            'Nombre de cas': 'Nombre de cas',
            col_groupe: col_groupe
        },
        text='label_text',
        color_discrete_sequence=px.colors.qualitative.Set1
    )

    fig.update_traces(
        texttemplate='%{text}',
        textposition='outside'
    )

    max_val = max(abs(counts['Nombre de cas']))
    fig.update_layout(
        xaxis=dict(
            tickvals=[-max_val, 0, max_val],
            ticktext=[str(max_val), '0', str(max_val)]
        ),
        bargap=0.1,
        template='plotly_white',
        yaxis=dict(categoryorder='array', categoryarray=ordre_categories)
    )

    fig.show()

# Fonction pour tracer la pyramide des âges
def graphique_pyramide_age(
    df: pd.DataFrame,
    col_tranche: str = "Tranche_age",
    col_sexe: str = "Sexe",
    col_valeur: str = "Nombre",
    valeurs_neg: Optional[List[str]] = None,
    titre: Optional[str] = "Pyramide des âges",
    seuil_min: int = 0,
    afficher_signe_negatif: bool = True,
    afficher_signe_negatif_dans_label: bool = True,
    croissant: bool = True,
    couleurs_personnalisees: Optional[Dict[str, str]] = None,
    annot: bool = False,
    facette_col: Optional[str] = None,
    taille_fig: Tuple[int, int] = (1200, 700),
    return_fig: bool = False,
    couleur_contour_facette: str = "#777772"
) -> Optional[px.bar]:
    """
    Trace une pyramide des âges symétrique à barres horizontales avec support de facettes.

    Agrège les données par tranche d’âge, sexe, et facette éventuelle.
    Si col_valeur n’est pas numérique, compte les occurrences.

    Paramètres :
    -----------
    df : pd.DataFrame
        DataFrame contenant les données source.
    col_tranche : str, optionnel (par défaut "Tranche_age")
        Nom de la colonne des catégories d'âge (axe Y).
    col_sexe : str, optionnel (par défaut "Sexe")
        Nom de la colonne des groupes à comparer (ex: Sexe).
    col_valeur : str, optionnel (par défaut "Nombre")
        Nom de la colonne contenant les valeurs numériques à sommer,
        ou colonne catégorielle à compter.
    valeurs_neg : list de str, optionnel
        Liste des valeurs dans col_sexe dont les valeurs seront négatives (ex: ["Homme"]).
    titre : str, optionnel
        Titre du graphique.
    seuil_min : int, optionnel (par défaut 0)
        Seuil minimal des valeurs pour être incluses dans le graphique.
    afficher_signe_negatif : bool, optionnel (par défaut True)
        Applique ou non le signe négatif sur les valeurs spécifiées dans valeurs_neg.
    afficher_signe_negatif_dans_label : bool, optionnel (par défaut True)
        Affiche ou non le signe négatif dans les annotations de texte.
    croissant : bool, optionnel (par défaut True)
        Définit si l'ordre des tranches d'âge est croissant (True) ou décroissant (False).
    couleurs_personnalisees : dict, optionnel
        Dictionnaire de correspondance catégorie -> couleur (ex: {"Homme": "#636efa"}).
    annot : bool, optionnel (par défaut False)
        Affiche les valeurs en annotations sur les barres si True.
    facette_col : str, optionnel
        Nom de la colonne pour créer des facettes (ex: "Province").
    taille_fig : tuple(int, int), optionnel (par défaut (1200, 700))
        Taille de la figure en pixels : (largeur, hauteur).
    return_fig : bool, optionnel (par défaut False)
        Retourne la figure Plotly si True, sinon affiche directement le graphique.
    couleur_contour_facette : str, optionnel (par défaut "#000000")
        Couleur hexadécimale pour le contour des facettes.

    Retour :
    --------
    plotly.graph_objs._figure.Figure ou None
        Figure Plotly créée ou None si erreur ou données vides.
        
    Exemple :
            fig = graphique_pyramide_age(
            df=df_viz_filtre_semaine,
            col_tranche='Tranche_age',
            col_sexe='Sexe',
            col_valeur='Unite_age',
            valeurs_neg=["Masculin"],
            titre=f"Distribution par tranche d'âge et sexe des cas de {nom_maladie} en RDC (SE01 à SE31)",
            seuil_min=10,
            croissant=False,
            afficher_signe_negatif_dans_label=False,
            facette_col='Province_notification',
            annot=True,
        )
    """

    df = df.copy()

    # Vérifier colonnes
    for c in [col_tranche, col_sexe, col_valeur]:
        if c not in df.columns:
            print(f"[ERROR] Colonne '{c}' absente dans le DataFrame")
            return None
    if facette_col is not None and facette_col not in df.columns:
        print(f"[ERROR] Colonne de facettage '{facette_col}' absente dans le DataFrame")
        return None

    # Nettoyage valeurs nulles
    df = df.dropna(subset=[col_tranche, col_sexe])
    if facette_col:
        df = df.dropna(subset=[facette_col])

    # Colonnes pour groupby
    group_cols = [col_tranche, col_sexe]
    if facette_col is not None:
        group_cols.append(facette_col)

    # Agrégation : somme si numérique, sinon comptage
    if pd.api.types.is_numeric_dtype(df[col_valeur]):
        agg_df = df.groupby(group_cols)[col_valeur].sum().reset_index()
    else:
        agg_df = df.groupby(group_cols).size().reset_index(name=col_valeur)

    # Filtrage par seuil_min
    agg_df = agg_df[agg_df[col_valeur] >= seuil_min]
    if agg_df.empty:
        print("[INFO] Aucune donnée après filtrage avec seuil_min")
        return None

    # Appliquer signe négatif
    if valeurs_neg is not None and afficher_signe_negatif:
        valeurs_neg_set = {v.lower() for v in valeurs_neg}
        agg_df[col_valeur] = agg_df.apply(
            lambda row: -row[col_valeur] if str(row[col_sexe]).lower() in valeurs_neg_set else row[col_valeur],
            axis=1
        )

    # Labels texte
    if afficher_signe_negatif_dans_label:
        agg_df['label_text'] = agg_df[col_valeur].astype(str)
    else:
        agg_df['label_text'] = agg_df[col_valeur].abs().astype(str)

    # Ordre catégories
    if not pd.api.types.is_categorical_dtype(agg_df[col_tranche]):
        categories = sorted(agg_df[col_tranche].unique(), reverse=not croissant)
        agg_df[col_tranche] = pd.Categorical(agg_df[col_tranche], categories=categories, ordered=True)
    else:
        cat_order = list(agg_df[col_tranche].cat.categories)
        if not croissant:
            cat_order = cat_order[::-1]
        agg_df[col_tranche] = agg_df[col_tranche].cat.reorder_categories(cat_order, ordered=True)

    # Couleurs par défaut
    if couleurs_personnalisees is None:
        couleurs_personnalisees = {
            "Masculin": "#1a1e2b",
            "Feminin": "#E70B0B"
        }
    for cat in agg_df[col_sexe].unique():
        if cat not in couleurs_personnalisees:
            couleurs_personnalisees[cat] = None

    # Création graphique
    fig = px.bar(
        agg_df,
        y=col_tranche,
        x=col_valeur,
        color=col_sexe,
        orientation='h',
        text='label_text' if annot else None,
        color_discrete_map=couleurs_personnalisees,
        facet_col=facette_col,
        facet_col_wrap=4 if facette_col else None,
        title=titre,
        labels={col_valeur: "Nombre", col_tranche: "Tranche d'âge", col_sexe: "Sexe"},
        category_orders={col_tranche: agg_df[col_tranche].cat.categories.tolist()},
        width=taille_fig[0],
        height=taille_fig[1]
    )

    max_val = max(abs(agg_df[col_valeur])) if not agg_df.empty else 0
    fig.update_layout(
        template="plotly_white",
        xaxis=dict(
            tickvals=[-max_val, 0, max_val],
            ticktext=[str(int(max_val)), "0", str(int(max_val))],
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor='LightGrey',
        ),
        yaxis=dict(autorange="reversed"),
        bargap=0.1,
        bargroupgap=0,
        title_x=0.5,
        margin=dict(t=80, b=80, l=80, r=80),
    )

    if annot:
        fig.update_traces(textposition='outside', cliponaxis=False)

    if facette_col:
        fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))

    # 📦 Encadrer chaque facette par un contour de couleur personnalisée
    for axis in fig.layout:
        if isinstance(fig.layout[axis], go.layout.XAxis) and "domain" in fig.layout[axis]:
            yaxis_name = axis.replace("xaxis", "yaxis")
            if yaxis_name in fig.layout and "domain" in fig.layout[yaxis_name]:
                x0, x1 = fig.layout[axis].domain
                y0, y1 = fig.layout[yaxis_name].domain
                fig.add_shape(
                    type="rect",
                    x0=x0, x1=x1,
                    y0=y0, y1=y1,
                    xref="paper", yref="paper",
                    line=dict(color=couleur_contour_facette, width=1),
                    fillcolor="rgba(0,0,0,0)"
                )

    if return_fig:
        return fig
    else:
        fig.show()
        return None

# Histogramme et courbes
def plot_evolution_multi_auto(
    df: pd.DataFrame,
    col_x: str = "Semaine_epi",
    courbe_col: List[str] = [],
    valeurs_courbe_col: Optional[Dict[str, Union[str, bool, int]]] = None,
    titre: Optional[str] = None,
    taille_fig: Tuple[int, int] = (1000, 600),
    couleurs: Optional[Dict[str, str]] = None,
    annot_x: bool = False,
    annot_y: bool = False,
    rotation: int = 0,
    marker_size: int = 8,
    pas_x: Optional[int] = None,
    afficher_legende: bool = True,
    seuil_min: int = 0,
    bargap: float = 0.2,
    bargroupgap: float = 0.1    
) -> Optional[go.Figure]:
    """
    Trace un graphique combiné (barres + courbes) en gérant automatiquement
    les colonnes numériques et catégorielles.
    
    Args :
        df : DataFrame contenant les données.
        col_x : Colonne catégorielle ou temporelle pour l'axe X.
        valeurs_courbe_col : Dictionnaire {colonne: valeur_à_compter} pour colonnes catégorielles.
            Exemple : {'Femme_enceinte': 'oui', 'Test_pos': True}
        courbe_col : Colonnes à tracer en courbe (numériques ou catégorielles).
        titre : Titre du graphique.
        taille_fig : Taille du graphique (largeur, hauteur).
        couleurs : Dictionnaire de couleurs pour les séries.
        annot_x : Afficher les valeurs sur l'axe X.
        annot_y : Afficher les valeurs sur l'axe Y (courbes).
        rotation : Rotation des labels de l'axe X.
        marker_size : Taille des marqueurs.
        pas_x : Pas d'affichage sur l'axe X.
        afficher_legende : Afficher la légende ou non.
        seuil_min : Seuil minimal d'occurrences sur l'axe X.
        bargap : Espacement entre groupes de barres.
        bargroupgap : Espacement entre barres dans un groupe.

    
    Returns :
        plotly.graph_objs.Figure ou None
    """

    valeurs_courbe_col = valeurs_courbe_col or {}

    # Vérification des colonnes
    colonnes_absentes = [col for col in [col_x] + courbe_col if col not in df.columns]
    if colonnes_absentes:
        print(f"[ERREUR] Colonnes absentes du DataFrame : {colonnes_absentes}")
        return None

    couleurs = couleurs or {"cas": "rgba(0, 123, 255, 0.6)"}
    for col in courbe_col:
        if col not in couleurs:
            couleurs[col] = None

    # Nettoyage et filtrage sur col_x
    df_clean = df[[col_x] + courbe_col].copy().dropna(subset=[col_x])

    # Comptage des cas par col_x (barres)
    cas_par_x = df_clean[col_x].value_counts().sort_index()
    cas_par_x = cas_par_x[cas_par_x >= seuil_min]
    if cas_par_x.empty:
        print("[INFO] Aucun groupe ne dépasse le seuil minimal.")
        return None

    # Préparation des données des courbes
    data_courbes = pd.DataFrame(index=cas_par_x.index)

    for col in courbe_col:
        if pd.api.types.is_numeric_dtype(df_clean[col]):
            # Somme pour colonnes numériques
            tmp = df_clean.groupby(col_x)[col].sum()
            tmp = tmp.reindex(cas_par_x.index, fill_value=0)
            data_courbes[col] = tmp
        else:
            # Colonne catégorielle => compter les occurrences de la valeur positive
            val_pos = valeurs_courbe_col.get(col)
            if val_pos is None:
                # Pas de valeur positive définie, compter les occurrences globales
                tmp = df_clean.groupby(col_x)[col].apply(lambda x: x.notna().sum())
                tmp = tmp.reindex(cas_par_x.index, fill_value=0)
                data_courbes[col] = tmp
            else:
                # Compter occurrences de la valeur positive
                tmp = df_clean[df_clean[col] == val_pos].groupby(col_x)[col].count()
                tmp = tmp.reindex(cas_par_x.index, fill_value=0)
                data_courbes[col] = tmp

    # Création de la figure
    fig = go.Figure()

    # Histogramme pour les cas
    fig.add_trace(go.Bar(
        x=cas_par_x.index,
        y=cas_par_x.values,
        name="Cas",
        marker_color=couleurs.get("cas"),
        yaxis='y1',
        text=cas_par_x.values if annot_x else None,
        textposition="auto" if annot_x else None
    ))

    # Courbes
    for col in courbe_col:
        fig.add_trace(go.Scatter(
            x=data_courbes.index,
            y=data_courbes[col],
            name=col,
            mode="lines+markers+text" if annot_y else "lines+markers",
            marker=dict(size=marker_size, color=couleurs.get(col)),
            yaxis='y2',
            text=[f"{v}" for v in data_courbes[col]] if annot_y else None,
            textposition="top center" if annot_y else None
        ))

    # Configuration layout
    fig.update_layout(
        title=titre or f"Évolution par '{col_x}'",
        xaxis=dict(
            title=col_x,
            tickangle=rotation,
            tickmode='linear',
            dtick=pas_x if pas_x else None,
            showgrid=True,              # active la grille verticale
            gridcolor='LightGray',      # couleur de la grille verticale
            gridwidth=1                 # épaisseur
        ),
        yaxis=dict(
            title="Nombre de cas",
            showgrid=True,              # active la grille horizontale
            gridcolor='LightGray',      # couleur de la grille horizontale
            gridwidth=1                 # épaisseur
        ),
        yaxis2=dict(
            title="Valeurs des courbes",
            overlaying='y',
            side='right',
            showgrid=False
        ),
        legend=dict(
            x=1.02,
            y=1,
            xanchor='left',
            yanchor='top',
            traceorder='normal',
            font=dict(size=12),
            borderwidth=1
        ) if afficher_legende else dict(visible=False),
        barmode='group',
        bargap=bargap,
        bargroupgap=bargroupgap,
        width=taille_fig[0],
        height=taille_fig[1],
        margin=dict(l=60, r=100 if afficher_legende else 20, t=60, b=60)
    )

    fig.show()