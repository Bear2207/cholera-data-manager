Guide d’utilisation moderne du stack Cholera Data Manager :

1. Démarrer l’environnement :
   - docker compose up -d
   - ou powershell -ExecutionPolicy Bypass -File .\scripts\start-stack.ps1
2. Charger les données dans PostgreSQL :
   - installer les dépendances Python si nécessaire :
     `pip install -r requirements.txt`
   - exécuter `python scripts/load_data.py`
3. Ouvrir l’interface :
   - PgAdmin : http://localhost:5050

Identifiants par défaut :
- PostgreSQL : utilisateur bearing / mot de passe Couspdata / base ids_db
- PgAdmin : data.analyse@cousp.org / DataCousp
- Superset : admin / Admin123

Services inclus :
- PostgreSQL + PostGIS pour les données géographiques
- pgAdmin pour administrer la base
- Metabase pour les tableaux de bord
- Superset pour l’analyse et la visualisation avancée

👉 Cette version offre un environnement complet, reproductible et prêt pour la collecte, l’import, l’analyse et la diffusion des données.
