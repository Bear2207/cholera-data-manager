Ton guide d’utilisation :

docker-compose up -d → lance tout l’environnement.

Mettre ton Excel brut dans le dossier scripts/, lancer excel_to_csv.py.

Le CSV se retrouve dans db/data/.

Importer avec psql -U admin -d cholera_db -f scripts/import_csv.sql.

Connecter Excel ou Metabase pour visualiser.

👉 Avec ça tu as une stack complète : collecte → base de données → dashboards → rapports.
