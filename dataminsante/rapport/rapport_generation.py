# -*- coding: utf-8 -*-

# dataminsante/rapport_generation.py

import os
import base64
import tempfile
from pathlib import Path
from typing import List, Tuple, Optional, Dict
import logging
import nbformat
import unicodedata
from fpdf import FPDF

logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

def nettoyer_texte(texte: str) -> str:
    """
    Nettoie le texte pour éviter les erreurs d'encodage dans le PDF.
    """
    texte = unicodedata.normalize("NFKD", texte)
    texte = texte.encode("latin-1", errors="ignore").decode("latin-1")
    return texte

class RapportPDF(FPDF):
    def __init__(self):
        super().__init__()
        # Police DejaVu pour support UTF-8 amélioré (fournir le fichier .ttf dans dataminsante/fonts)
        font_path = Path(__file__).parent / "fonts" / "DejaVuSans.ttf"
        if font_path.exists():
            self.add_font("DejaVu", "", str(font_path), uni=True)
            self.set_font("DejaVu", size=12)
        else:
            self.set_font("Arial", size=12)
            logger.warning("Police DejaVu non trouvée, utilisation Arial standard.")

    def header(self):
        self.set_font("DejaVu" if "DejaVu" in self.font_families else "Arial", "B", 14)
        self.cell(0, 10, "Rapport Epidémiologique", ln=1, align="C")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("DejaVu" if "DejaVu" in self.font_families else "Arial", "I", 8)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')

    def ajouter_titre(self, titre: str):
        self.set_font("DejaVu" if "DejaVu" in self.font_families else "Arial", "B", 12)
        self.cell(0, 10, nettoyer_texte(titre), ln=1)

    def ajouter_texte(self, texte: str):
        self.set_font("DejaVu" if "DejaVu" in self.font_families else "Arial", size=11)
        self.multi_cell(0, 8, nettoyer_texte(texte))
        self.ln(2)

    def ajouter_image(self, chemin: str, largeur: int = 160):
        if Path(chemin).exists():
            self.image(chemin, w=largeur)
            self.ln(10)
        else:
            logger.warning(f"Image non trouvée : {chemin}")

    def ajouter_tableau(self, data: List[List[str]], largeur_totale: int = 180):
        """
        Ajoute un tableau au PDF avec largeur dynamique des colonnes.
        """
        if not data or not all(isinstance(row, list) for row in data):
            logger.warning("Données du tableau invalides ou vides.")
            return

        self.set_font("DejaVu" if "DejaVu" in self.font_families else "Arial", size=10)

        nb_colonnes = len(data[0])
        largeur_col = largeur_totale // nb_colonnes

        # En-tête
        self.set_fill_color(200, 220, 255)
        for cell in data[0]:
            self.cell(largeur_col, 8, nettoyer_texte(cell), border=1, fill=True)
        self.ln()

        # Corps
        self.set_fill_color(255, 255, 255)
        for row in data[1:]:
            for cell in row:
                self.cell(largeur_col, 7, nettoyer_texte(cell), border=1, fill=True)
            self.ln()

def sauvegarder_fig_plotly(fig, chemin: str) -> None:
    try:
        fig.write_image(chemin, format='png', scale=2)
        logger.info(f"Graphique Plotly sauvegardé : {chemin}")
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde du graphique Plotly : {e}")

def sauvegarder_fig_matplotlib(fig, chemin: str) -> None:
    try:
        fig.savefig(chemin, bbox_inches='tight')
        fig.clf()
        logger.info(f"Graphique Matplotlib sauvegardé : {chemin}")
    except Exception as e:
        logger.error(f"Erreur sauvegarde graphique Matplotlib : {e}")

def generer_rapport_complet(
    pdf_path: str,
    resume: str,
    images: List[Tuple[str, str]],
    tableau: Optional[List[List[str]]] = None,
    meta: Optional[Dict[str, str]] = None,
):
    """
    Génère un rapport PDF complet avec métadonnées, résumé, tableau, et images.

    Args:
        pdf_path (str): chemin de sortie du PDF.
        resume (str): texte résumé.
        images (List[Tuple[str, str]]): liste (titre, chemin_image).
        tableau (Optional[List[List[str]]]): tableau sous forme liste de listes (première ligne = entête).
        meta (Optional[Dict[str, str]]): métadonnées (ex : auteur, date, titre).
    """
    pdf = RapportPDF()
    pdf.add_page()

    if meta:
        pdf.ajouter_titre("Métadonnées")
        for cle, valeur in meta.items():
            pdf.ajouter_texte(f"{cle} : {valeur}")
        pdf.ln(5)

    if resume:
        pdf.ajouter_titre("Résumé")
        pdf.ajouter_texte(resume)

    if tableau:
        pdf.ajouter_titre("Synthèse des données")
        pdf.ajouter_tableau(tableau)

    for titre, img_path in images:
        pdf.ajouter_titre(titre)
        pdf.ajouter_image(img_path)

    pdf.output(pdf_path)
    logger.info(f"Rapport complet généré : {pdf_path}")

def notebook_vers_pdf(path_ipynb: str, pdf_path: str):
    """
    Extrait le contenu d'un notebook (.ipynb) et le convertit en PDF.
    Gère textes markdown, sorties de code texte et images PNG encodées base64.
    """
    with open(path_ipynb, "r", encoding="utf-8") as f:
        notebook = nbformat.read(f, as_version=4)

    pdf = RapportPDF()
    pdf.add_page()

    for cell in notebook.cells:
        if cell.cell_type == "markdown":
            pdf.ajouter_texte(cell.source)
        elif cell.cell_type == "code" and "outputs" in cell:
            for output in cell.outputs:
                if output.output_type == "stream" and "text" in output:
                    pdf.ajouter_texte(output["text"])
                elif output.output_type == "display_data" and "image/png" in output.get("data", {}):
                    image_data = output["data"]["image/png"]
                    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_img:
                        tmp_img.write(base64.b64decode(image_data))
                        tmp_img_path = tmp_img.name
                    pdf.ajouter_image(tmp_img_path)
                    os.remove(tmp_img_path)

    pdf.output(pdf_path)
    logger.info(f"Rapport PDF extrait du notebook : {pdf_path}")
