import pandas as pd
from pathlib import Path

# Chemin absolu vers ton fichier
fichier_excel = Path("/home/bearing/projects/cholera-data-manager/db/IDS_RDC.xlsx")
feuille = "IDS_RDC"

# Lire le fichier Excel avec openpyxl
df = pd.read_excel(fichier_excel, sheet_name=feuille, engine="openpyxl")

# Renommer les colonnes
df.rename(columns={
    "PAYS": "pays",
    "PROV": "province",
    "ZS": "zone_sante",
    "POP": "population",
    "NUMSEM": "num_semaine",
    "DEBUTSEM": "debut_semaine",
    "MALADIE": "maladie",
    "TOTALCAS": "cas_total",
    "TOTALDECES": "deces_total",
    "LETAL": "letalite",
    "ATTAQ": "taux_attaque"
}, inplace=True)

# Conserver uniquement les colonnes utiles
colonnes = [
    "pays", "province", "zone_sante", "population",
    "num_semaine", "debut_semaine", "maladie",
    "cas_total", "deces_total", "letalite", "taux_attaque"
]
df = df[colonnes]

# Nettoyer les types de données
df["population"] = df["population"].fillna(0).astype(int)
df["cas_total"] = df["cas_total"].fillna(0).astype(int)
df["deces_total"] = df["deces_total"].fillna(0).astype(int)
df["letalite"] = (df["letalite"] * 100).round().astype(float)
df["taux_attaque"] = df["taux_attaque"].fillna(0).astype(float)

# Export en CSV
fichier_csv = Path("/home/bearing/projects/cholera-data-manager/db/data/donnees_maladie.csv")
df.to_csv(fichier_csv, index=False)

print(f"✅ CSV généré : {fichier_csv}")
