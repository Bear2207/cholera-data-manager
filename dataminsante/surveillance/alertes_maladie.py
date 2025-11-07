# --------------------------------------
# Surveillance médias avec GDELT Project + Filtre pays optionnel
# Auteur : [Ton Nom]
# --------------------------------------

import requests
import pandas as pd
from datetime import datetime, timedelta

# ========= PARAMÈTRES =========
keyword = "Ebola"         # Mot-clé à rechercher
days_back = 3            # Nombre de jours à remonter
max_results = 50         # Nombre maximum d’articles à récupérer
country_filter = "CD"      # Code pays ISO2 (ex. 'CD' = RDC, 'FR' = France, vide = tous pays)
output_csv = "gdelt_resultats.csv"

# ========= CONSTRUCTION REQUÊTE =========
base_url = "https://api.gdeltproject.org/api/v2/doc/doc"

end_date = datetime.utcnow()
start_date = end_date - timedelta(days=days_back)
end_str = end_date.strftime("%Y%m%d%H%M%S")
start_str = start_date.strftime("%Y%m%d%H%M%S")

# Si un pays est défini, on ajoute le filtre dans la requête
if country_filter:
    search_query = f"{keyword} sourcecountry:{country_filter}"
else:
    search_query = keyword

params = {
    "query": search_query,
    "mode": "ArtList",
    "maxrecords": max_results,
    "format": "JSON",
    "sort": "DateDesc",
    "startdatetime": start_str,
    "enddatetime": end_str
}

# ========= REQUÊTE API =========
print(f"Recherche de '{keyword}' sur les {days_back} derniers jours"
      + (f" pour le pays {country_filter}" if country_filter else " (tous pays)..."))
response = requests.get(base_url, params=params)

if response.status_code != 200:
    print("❌ Erreur API GDELT :", response.status_code)
    exit()

data = response.json()
articles = data.get("articles", [])

# ========= TRAITEMENT =========
if not articles:
    print("Aucun article trouvé.")
else:
    df = pd.DataFrame(articles)
    df = df[["seendate", "sourcecountry", "title", "url"]]
    df.rename(columns={
        "seendate": "Date",
        "sourcecountry": "Pays",
        "title": "Titre",
        "url": "Lien"
    }, inplace=True)

    # Sauvegarde CSV
    df.to_csv(output_csv, index=False, encoding="utf-8-sig")
    print(f"✅ {len(df)} articles sauvegardés dans {output_csv}")

    # Aperçu
    print(df.head())
