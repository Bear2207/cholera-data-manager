import re

def normaliser_valeur(s):
    """Nettoie et met en forme une valeur texte :
    - strip espaces
    - remplace - et _ par espace
    - réduit les espaces multiples
    - met la première lettre de chaque mot en majuscule
    """
    s = s.strip()
    s = re.sub(r"[-_]", " ", s)       # - et _ → espace
    s = re.sub(r"\s+", " ", s)        # espaces multiples → un seul
    s = s.title()                     # Majuscule en début de mot
    return s

def comparer_listes(ref_list, df_list):
    """
    Compare deux listes avec correction automatique de casse et d'espaces.
    """
    ref_norm = {normaliser_valeur(p): p for p in ref_list}
    df_norm = {normaliser_valeur(p): p for p in df_list}
    
    manquantes = [ref_norm[k] for k in ref_norm if k not in df_norm]
    en_trop = [df_norm[k] for k in df_norm if k not in ref_norm]
    correspondances = {df_norm[k]: ref_norm[k] for k in df_norm if k in ref_norm}
    
    return {
        "manquantes": sorted(manquantes),
        "en_trop": sorted(en_trop),
        "correspondances": correspondances
    }

def calculer_completude(ref_list, df_list):
    """
    Calcule la complétude et liste les manquants après normalisation + title case.
    """
    ref_norm = {normaliser_valeur(p): p for p in ref_list}
    df_norm = {normaliser_valeur(p): p for p in df_list}
    
    nb_trouves = sum(1 for k in ref_norm if k in df_norm)
    nb_attendus = len(ref_norm)
    completude = nb_trouves / nb_attendus if nb_attendus > 0 else 0.0
    
    manquantes = [ref_norm[k] for k in ref_norm if k not in df_norm]
    
    return {
        "nb_attendus": nb_attendus,
        "nb_reçus": nb_trouves,
        "completude_%": round(completude * 100, 2),
        "manquantes": sorted(manquantes)
    }
