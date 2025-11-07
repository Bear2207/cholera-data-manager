"""Wrappers pour fonctions de visualisation (repose sur dataminsante.visualisation).
"""
from dataminsante.visualisation import *
import pandas as pd


def plot_evolution_histogramme(df: pd.DataFrame, **kwargs):
    return plot_histogramme_groupe_interactif_empile(df, **kwargs)


def plot_pyramide(df: pd.DataFrame, **kwargs):
    return plot_pyramide_symetrique(df=df, **kwargs)

# Ajoute d'autres wrappers si nécessaire