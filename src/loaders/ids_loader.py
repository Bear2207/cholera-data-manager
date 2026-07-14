import pandas as pd
from pathlib import Path

IDS_COLUMNS = [
    'code_zone', 'pays', 'province', 'zone_sante', 'population', 'num_semaine',
    'annee', 'debut_semaine_originale', 'debut_semaine', 'maladie', 'cas_tnn',
    'deces_tnn', 'cas_0_11_mois', 'deces_0_11_mois', 'cas_12_59_mois',
    'deces_12_59_mois', 'cas_5_15_ans', 'deces_5_15_ans', 'cas_15_plus',
    'deces_15_plus', 'taux_attaque', 'rec_status', 'unique_key'
]

def _week_start_dates(df: pd.DataFrame) -> pd.Series:
    if not {'annee', 'num_semaine'}.issubset(df.columns):
        return pd.Series(pd.NaT, index=df.index)
    years = pd.to_numeric(df['annee'], errors='coerce').astype('Int64').astype(str)
    weeks = pd.to_numeric(df['num_semaine'], errors='coerce').astype('Int64').astype(str).str.zfill(2)
    return pd.to_datetime(years + '-W' + weeks + '-1', format='%G-W%V-%u', errors='coerce')

def load_ids_excel(filepath: Path) -> pd.DataFrame:
    """Charge le fichier IDS et l'aligne sur les colonnes insérables."""
    if not filepath.exists():
        raise FileNotFoundError(f"Fichier IDS introuvable : {filepath}")
    df = pd.read_excel(filepath, sheet_name='IDS_RDC', engine='openpyxl')
    # On renomme les colonnes pour correspondre au schéma
    rename_map = {
        'NUM': 'code_zone', 'PAYS': 'pays', 'PROV': 'province', 'ZS': 'zone_sante',
        'POP': 'population', 'NUMSEM': 'num_semaine', 'DEBUTSEM': 'debut_semaine_originale',
        'MALADIE': 'maladie', 'C328TNN': 'cas_tnn', 'DTNN': 'deces_tnn',
        'C011MOIS': 'cas_0_11_mois', 'D011MOIS': 'deces_0_11_mois',
        'C1259MOIS': 'cas_12_59_mois', 'D1259MOIS': 'deces_12_59_mois',
        'C515ANS': 'cas_5_15_ans', 'D515ANS': 'deces_5_15_ans',
        'CP15ANS': 'cas_15_plus', 'DP15ANS': 'deces_15_plus',
        'TOTALCAS': 'cas_total', 'TOTALDECES': 'deces_total',
        'LETAL': 'letalite', 'ATTAQ': 'taux_attaque',
        'RecStatus': 'rec_status', 'UniqueKey': 'unique_key', 'ANNEE': 'annee'
    }
    df = df.rename(columns=rename_map)
    debut_from_file = pd.to_datetime(df.get('debut_semaine_originale'), errors='coerce')
    df['debut_semaine_originale'] = debut_from_file.dt.date
    df['debut_semaine'] = debut_from_file.fillna(_week_start_dates(df)).dt.date
    return df[[col for col in IDS_COLUMNS if col in df.columns]]