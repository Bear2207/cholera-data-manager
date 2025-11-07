# dataminsante/visualisation_carte.py

import geopandas as gpd  # manipulation des données géographiques
import pandas as pd
import folium  # cartes interactives (type OpenStreetMap)
import matplotlib.pyplot as plt
import contextily as ctx  # fonds de carte basés sur des tuiles Web
import logging
from shapely import wkt
from shapely.geometry import Point

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

def detecter_colonnes_coordonnees(df: pd.DataFrame):
    """
    Tente d'identifier automatiquement les colonnes de coordonnées géographiques.
    
    Détection basée sur :
    - Colonnes nommées 'Latitude' / 'Longitude'
    - Colonne contenant du WKT (POINT(...))

    Returns:
        Tuple (mode, colonne1, colonne2) où mode ∈ {'latlon', 'wkt'}
    """
    colonnes = df.columns.str.lower()
    lat_col = next((col for col in df.columns if col.lower() in ['lat', 'latitude','Latitude']), None)
    lon_col = next((col for col in df.columns if col.lower() in ['lon', 'lng', 'longitude','Longitude']), None)
    point_col = next((col for col in df.columns if df[col].astype(str).str.startswith('POINT').any()), None)

    if lat_col and lon_col:
        return ('latlon', lat_col, lon_col)
    elif point_col:
        return ('wkt', point_col, None)
    else:
        return (None, None, None)

def convertir_en_geodataframe(df: pd.DataFrame) -> gpd.GeoDataFrame:
    """
    Convertit un DataFrame contenant des coordonnées géographiques en GeoDataFrame.

    Supporte :
    - Latitude/Longitude en colonnes séparées
    - Colonne texte contenant des objets WKT de type POINT

    Args:
        df: DataFrame standard avec données géographiques

    Returns:
        GeoDataFrame avec géométrie et système de coordonnées EPSG:4326
    """
    mode, col1, col2 = detecter_colonnes_coordonnees(df)

    if mode == 'latlon':
        try:
            df[col1] = pd.to_numeric(df[col1], errors='coerce')
            df[col2] = pd.to_numeric(df[col2], errors='coerce')
            df = df.dropna(subset=[col1, col2])
            geometry = [Point(xy) for xy in zip(df[col2], df[col1])]
            gdf = gpd.GeoDataFrame(df, geometry=geometry, crs='EPSG:4326')
            logging.info(f"Conversion réussie en GeoDataFrame via colonnes '{col1}' et '{col2}'.")
            return gdf
        except Exception as e:
            logging.error(f"Erreur de conversion GeoDataFrame (lat/lon) : {e}")

    elif mode == 'wkt':
        try:
            df['geometry'] = df[col1].apply(wkt.loads)
            gdf = gpd.GeoDataFrame(df, geometry='geometry', crs='EPSG:4326')
            logging.info(f"Conversion réussie en GeoDataFrame via colonne WKT '{col1}'.")
            return gdf
        except Exception as e:
            logging.error(f"Erreur de conversion GeoDataFrame (POINT WKT) : {e}")

    logging.warning("Aucune colonne géographique détectée pour la conversion.")
    return None

def convertir_excel_en_geodataframe(
    path: str,
    colonne_lat: str = "Latitude",
    colonne_lon: str = "Longitude",
    colonne_geometry: str = "localisation"
) -> gpd.GeoDataFrame:
    """
    Charge un fichier Excel avec des coordonnées géographiques et le convertit en GeoDataFrame.

    Args:
        path: Chemin vers le fichier Excel
        colonne_lat: Nom de la colonne latitude
        colonne_lon: Nom de la colonne longitude
        colonne_geometry: Nom de la colonne pour stocker la géométrie créée

    Returns:
        GeoDataFrame avec les points géographiques valides
    """
    try:
        df = pd.read_excel(path)
        df[colonne_lon] = pd.to_numeric(df[colonne_lon], errors="coerce")
        df[colonne_lat] = pd.to_numeric(df[colonne_lat], errors="coerce")

        nuls = df[[colonne_lon, colonne_lat]].isnull().sum()
        logging.info(f"Coordonnées manquantes: Longitude={nuls[colonne_lon]}, Latitude={nuls[colonne_lat]}")

        df = df.dropna(subset=[colonne_lon, colonne_lat])
        df[colonne_geometry] = df.apply(lambda row: Point(row[colonne_lon], row[colonne_lat]), axis=1)
        gdf = gpd.GeoDataFrame(df, geometry=colonne_geometry, crs="EPSG:4326")
        logging.info(f"{len(gdf)} points géographiques valides chargés depuis {path}")
        return gdf

    except Exception as e:
        logging.error(f"Erreur lors de la conversion Excel -> GeoDataFrame : {e}")
        return None

def afficher_points_sur_carte(
    gdf: gpd.GeoDataFrame,
    colonne_info: str = "Structure_sanitaire",
    colonnes_tooltip: list = None,
    fichier_html: str = "carte_points.html"
):
    """
    Affiche une carte interactive des points géographiques dans un fichier HTML.

    Args:
        gdf: GeoDataFrame contenant les points
        colonne_info: Colonne utilisée pour le coloriage
        colonnes_tooltip: Liste des colonnes à afficher en infobulle
        fichier_html: Chemin de sauvegarde de la carte
    """
    try:
        if colonnes_tooltip is None:
            colonnes_tooltip = [col for col in gdf.columns if col not in gdf.geometry.name]

        m = gdf.explore(
            column=colonne_info,
            legend=False,
            tooltip=colonnes_tooltip,
            cmap="Set1",
            style_kwds={"radius": 5}
        )
        m.save(fichier_html)
        logging.info(f"Carte enregistrée dans {fichier_html}")
    except Exception as e:
        logging.error(f"Erreur d'affichage de la carte : {e}")

def charger_carte(path_shapefile: str) -> gpd.GeoDataFrame:
    """
    Charge un shapefile ou GeoJSON représentant les entités géographiques.

    Args:
        path_shapefile: Chemin du fichier géographique

    Returns:
        GeoDataFrame contenant les entités
    """
    try:
        gdf = gpd.read_file(path_shapefile)
        logging.info(f"Carte chargée : {len(gdf)} entités.")
        return gdf
    except Exception as e:
        logging.error(f"Échec du chargement de la carte : {e}")
        return None

def joindre_donnees(
    carte_gdf: gpd.GeoDataFrame,
    df_donnees: pd.DataFrame,
    colonne_cle_geo: str,
    colonne_cle_data: str,
    colonne_valeurs: str = 'cas'
) -> gpd.GeoDataFrame:
    """
    Joint les données tabulaires aux entités géographiques (zones, provinces, etc.).

    Args:
        carte_gdf: GeoDataFrame des entités géographiques
        df_donnees: DataFrame contenant les données (cas, population, etc.)
        colonne_cle_geo: Colonne géo (clé primaire pour la jointure côté géographique)
        colonne_cle_data: Colonne de la table de données (clé secondaire)
        colonne_valeurs: Colonne numérique à joindre

    Returns:
        GeoDataFrame enrichi
    """
    try:
        for col in [colonne_cle_geo]:
            if col not in carte_gdf.columns:
                raise KeyError(f"Colonne '{col}' absente de la carte géographique.")
        for col in [colonne_cle_data, colonne_valeurs]:
            if col not in df_donnees.columns:
                raise KeyError(f"Colonne '{col}' absente des données tabulaires.")

        df_grouped = df_donnees[[colonne_cle_data, colonne_valeurs]] \
            .groupby(colonne_cle_data).sum().reset_index()
        gdf = carte_gdf.merge(df_grouped, left_on=colonne_cle_geo, right_on=colonne_cle_data, how='left')
        gdf[colonne_valeurs] = gdf[colonne_valeurs].fillna(0)
        logging.info(f"Données jointes : {gdf.shape[0]} zones.")
        return gdf

    except Exception as e:
        logging.error(f"Problème de jointure : {e}")
        return carte_gdf

def carte_statique(
    gdf: gpd.GeoDataFrame,
    colonne_valeurs: str,
    titre: str = "Carte épidémiologique",
    output_path: str = None
):
    """
    Génère une carte statique colorée à partir d'un GeoDataFrame.

    Args:
        gdf: GeoDataFrame avec géométrie (polygones ou points)
        colonne_valeurs: Colonne numérique à afficher
        titre: Titre de la carte
        output_path: Fichier de sortie (PNG ou PDF), sinon affichage interactif
    """
    try:
        if colonne_valeurs not in gdf.columns:
            raise KeyError(f"Colonne '{colonne_valeurs}' non trouvée dans le GeoDataFrame.")

        if gdf.crs is None or gdf.crs.to_epsg() != 3857:
            gdf = gdf.to_crs(epsg=3857)

        fig, ax = plt.subplots(figsize=(12, 10))
        gdf.plot(
            column=colonne_valeurs,
            cmap='OrRd',
            linewidth=0.8,
            ax=ax,
            edgecolor='0.8',
            legend=True
        )
        ax.set_title(titre, fontsize=15)
        ax.axis('off')

        # Sécuriser l'ajout de fond de carte
        try:
            ctx.add_basemap(ax, source=ctx.providers.Stamen.TonerLite)
        except Exception as e:
            logging.warning(f"Fond de carte non chargé : {e}")

        if output_path:
            plt.savefig(output_path, dpi=300)
            logging.info(f"Carte enregistrée : {output_path}")
        else:
            plt.show()

    except Exception as e:
        logging.error(f"Impossible de générer la carte statique : {e}")

def carte_interactive(
    gdf: gpd.GeoDataFrame,
    colonne_valeurs: str,
    nom_zone: str = 'Province',
    output_path: str = None,
    gdf_polygones: gpd.GeoDataFrame = None
) -> folium.Map:
    """
    Crée une carte interactive Folium à partir d'un GeoDataFrame :
    - Points : affichage avec cercles et tooltip.
    - Polygones : carte choroplèthe.
    - Avec gdf_polygones : jointure + choroplèthe sur couche polygones externe.

    Args:
        gdf: GeoDataFrame avec géométrie (points ou polygones) et données.
        colonne_valeurs: Colonne numérique à afficher.
        nom_zone: Colonne clé (ex: province) pour jointure/affichage.
        output_path: Chemin de sauvegarde HTML (optionnel).
        gdf_polygones: GeoDataFrame polygones (optionnel).

    Returns:
        folium.Map ou None si erreur.
    """
    try:
        # Vérification des colonnes
        for col in [colonne_valeurs, nom_zone]:
            if col not in gdf.columns:
                raise KeyError(f"Colonne '{col}' manquante dans le GeoDataFrame.")

        # Géométrie non vide
        if gdf.geometry.is_empty.all():
            raise ValueError("Toutes les géométries sont vides.")

        # CRS en WGS84
        gdf = gdf.to_crs(epsg=4326)
        if gdf_polygones is not None:
            gdf_polygones = gdf_polygones.to_crs(epsg=4326)

        # Détection des types géométriques
        geom_types = gdf.geometry[~gdf.geometry.is_empty].geom_type.unique()

        # Centre de la carte
        if 'Point' in geom_types:
            center = [gdf.geometry.y.mean(), gdf.geometry.x.mean()]
        else:
            center = [gdf.geometry.unary_union.centroid.y, gdf.geometry.unary_union.centroid.x]

        m = folium.Map(location=center, zoom_start=7)

        # Cas polygones avec couche externe
        if gdf_polygones is not None:
            df_agg = gdf.groupby(nom_zone)[colonne_valeurs].sum().reset_index()
            gdf_polygones_merged = gdf_polygones.merge(df_agg, on=nom_zone, how='left').fillna(0)

            if gdf_polygones_merged[colonne_valeurs].sum() == 0:
                logging.warning("Somme des valeurs nulle dans la couche polygones.")

            folium.Choropleth(
                geo_data=gdf_polygones_merged.__geo_interface__,
                data=gdf_polygones_merged,
                columns=[nom_zone, colonne_valeurs],
                key_on=f"feature.properties.{nom_zone}",
                fill_color='YlOrRd',
                fill_opacity=0.7,
                line_opacity=0.2,
                legend_name=f"{colonne_valeurs} par {nom_zone}",
            ).add_to(m)

        # Cas polygones dans gdf
        elif set(geom_types).issubset({'Polygon', 'MultiPolygon'}):
            if gdf[colonne_valeurs].sum() == 0:
                logging.warning("Somme des valeurs nulle dans le GeoDataFrame.")

            folium.Choropleth(
                geo_data=gdf.__geo_interface__,
                data=gdf,
                columns=[nom_zone, colonne_valeurs],
                key_on=f"feature.properties.{nom_zone}",
                fill_color='YlOrRd',
                fill_opacity=0.7,
                line_opacity=0.2,
                legend_name=f"{colonne_valeurs} par {nom_zone}",
            ).add_to(m)

        # Cas points
        elif set(geom_types) == {'Point'}:
            for _, row in gdf.iterrows():
                if row.geometry.is_empty or row[colonne_valeurs] is None:
                    continue
                popup_text = f"{row[nom_zone]} : {row[colonne_valeurs]}"
                folium.CircleMarker(
                    location=[row.geometry.y, row.geometry.x],
                    radius=8,
                    popup=popup_text,
                    tooltip=popup_text,
                    color='blue',
                    fill=True,
                    fill_color='blue',
                    fill_opacity=0.7
                ).add_to(m)

        else:
            raise ValueError(f"Type(s) de géométrie(s) non supporté(s) : {geom_types}")

        if output_path:
            m.save(output_path)
            logging.info(f"Carte interactive sauvegardée : {output_path}")

        return m

    except Exception as e:
        logging.error(f"Erreur dans carte_interactive : {e}")
        return None


# Exemple d’appel
# m = carte_interactive(gdf, 'Cas', 'Province', 'output/carte.html', gdf_polygones=gdf_provinces)
# if m:
#     print("Carte créée")
# else:
#     print("Erreur lors de la création")