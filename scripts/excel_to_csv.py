import pandas as pd
from pathlib import Path
import datetime

# Paramètres
ANNEE_REF = 2026  # Année de référence pour calculer les semaines
fichier_excel = Path("/cholera-data-manager/db/IDS_RDC.xlsx")
feuille = "IDS_RDC"

# Lecture
df = pd.read_excel(fichier_excel, sheet_name=feuille, engine="openpyxl")

# Renommage des colonnes (inchangé)
df.rename(columns={
    "NUM": "code_zone",
    "PAYS": "pays",
    "PROV": "province",
    "ZS": "zone_sante",
    "POP": "population",
    "NUMSEM": "num_semaine",
    "DEBUTSEM": "debut_semaine_originale",  # on garde la colonne brute
    "MALADIE": "maladie",
    "C328TNN": "cas_tnn",
    "DTNN": "deces_tnn",
    "C011MOIS": "cas_0_11_mois",
    "D011MOIS": "deces_0_11_mois",
    "C1259MOIS": "cas_12_59_mois",
    "D1259MOIS": "deces_12_59_mois",
    "C515ANS": "cas_5_15_ans",
    "D515ANS": "deces_5_15_ans",
    "CP15ANS": "cas_15_plus",
    "DP15ANS": "deces_15_plus",
    "TOTALCAS": "cas_total",
    "TOTALDECES": "deces_total",
    "LETAL": "letalite",
    "ATTAQ": "taux_attaque",
    "RecStatus": "rec_status",
    "UniqueKey": "unique_key"
}, inplace=True)

# ---- Gestion des dates ----
# Option 2 : recalculer la date de début de semaine à partir de num_semaine et ANNEE_REF
# La fonction ci-dessous donne le lundi de la semaine ISO (semaine 1 = premier lundi de l'année)
def date_debut_semaine(annee, semaine):
    # On utilise la norme ISO : le premier lundi de l'année
    # On calcule le jour de la semaine du 4 janvier (première semaine ISO)
    premiere_semaine = datetime.date(annee, 1, 4)
    lundi_1 = premiere_semaine - datetime.timedelta(days=premiere_semaine.weekday())
    return lundi_1 + datetime.timedelta(weeks=semaine-1)

# Appliquer la fonction sur chaque ligne
df["debut_semaine"] = df.apply(
    lambda row: date_debut_semaine(ANNEE_REF, row["num_semaine"]) 
    if pd.notnull(row["num_semaine"]) and row["num_semaine"] > 0 else None,
    axis=1
)

# On peut aussi conserver la colonne originale pour vérification
# df["debut_semaine_originale"] = pd.to_datetime(df["debut_semaine_originale"], errors="coerce")

# ---- Sélection des colonnes finales ----
colonnes = [
    "code_zone", "pays", "province", "zone_sante", "population",
    "num_semaine", "debut_semaine", "maladie",
    "cas_tnn", "deces_tnn",
    "cas_0_11_mois", "deces_0_11_mois",
    "cas_12_59_mois", "deces_12_59_mois",
    "cas_5_15_ans", "deces_5_15_ans",
    "cas_15_plus", "deces_15_plus",
    "cas_total", "deces_total",
    "letalite", "taux_attaque",
    "rec_status", "unique_key"
]
df = df[colonnes]

# Nettoyage des types
for col in df.columns:
    if col in ["population", "num_semaine", "cas_tnn", "deces_tnn", 
               "cas_0_11_mois", "deces_0_11_mois", "cas_12_59_mois", 
               "deces_12_59_mois", "cas_5_15_ans", "deces_5_15_ans",
               "cas_15_plus", "deces_15_plus", "cas_total", "deces_total",
               "rec_status", "unique_key"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    elif col == "debut_semaine":
        df[col] = pd.to_datetime(df[col], errors="coerce")
    elif col in ["letalite", "taux_attaque"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

# Export
fichier_csv = Path("C:\\Users\\beari\\Documents\\cholera-data-manager\\cholera-data-manager\\db\\data\\donnees_maladie.csv")
df.to_csv(fichier_csv, index=False, na_rep="NULL")

print(f"✅ CSV généré avec dates recalculées pour l'année {ANNEE_REF} : {fichier_csv}")