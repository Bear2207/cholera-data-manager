import pandas as pd

# Lire le fichier Excel
file_path = "C:\\Users\\beari\\Documents\\cholera-data-manager\\db\\BDD.xlsx"
df = pd.read_excel(file_path, sheet_name="Cas_ll", engine="openpyxl")

# Supprimer les colonnes "Provenance" et "N" (si elles existent)
cols_to_drop = ["Provenance", "N"]
df.drop(columns=[col for col in cols_to_drop if col in df.columns], inplace=True, errors='ignore')

# Nettoyer les noms de colonnes : remplacer les espaces et caractères spéciaux par '_'
df.columns = df.columns.str.replace(' ', '_').str.replace('/', '_').str.replace('(', '').str.replace(')', '')

# Convertir les colonnes de date si nécessaire
date_cols = ['Date_arrivee_malade', 'Date_admission_au_CT', 'Date_notification', 
             'Date_investigation', 'Date_debut_maladie', 'Date_prelevement', 
             'Date_sortie_au_CT', 'Date_de_guerie']
for col in date_cols:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors='coerce').dt.date

# Exporter en CSV
output_csv = "C:\\Users\\beari\\Documents\\cholera-data-manager\\db\\data\\ll_cholera_data.csv"
df.to_csv(output_csv, index=False, na_rep='')
print(f"CSV généré : {output_csv} avec {len(df.columns)} colonnes et {len(df)} lignes.")