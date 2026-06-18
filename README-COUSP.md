Ton guide d’utilisation :

1. docker-compose up -d → lance tout l’environnement.
2. Mettre ton Excel brut dans le dossier scripts/, lancer excel_to_csv.py.
3. Le CSV se retrouve dans db/data/.
4. Importer avec PostgreSQL :
   - docker cp ./db/data/donnees_maladie.csv cousp_db:/tmp/donnees_maladie.csv
   - docker exec -it cousp_db psql -U bearing -d ids_db -f /scripts/import_csv.sql
5. Connecter Excel, Metabase ou Superset pour visualiser.

Services exposés :
- PgAdmin : http://localhost:5050 (email : data.analyse@cousp.org / mot de passe : DataCousp)
- Metabase : http://localhost:3000
- Superset : http://localhost:8088 (admin / Admin123)

👉 Avec cette stack tu as une solution complète : collecte → base de données → exploration & dashboards → rapports.
