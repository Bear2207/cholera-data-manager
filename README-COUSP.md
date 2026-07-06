Guide d’utilisation A → Z — Cholera Data Manager

Pré-requis
- Docker & Docker Compose installés
- Python 3.9+ (ou votre installation locale) pour les scripts de chargement et de nettoyage

1) Démarrer la stack

   docker compose up -d

ou sous PowerShell:

   powershell -ExecutionPolicy Bypass -File .\scripts\start-stack.ps1

Vérifier le statut des services:

   docker compose ps

2) Préparer l'environnement Python

Option recommandée: créer un virtualenv puis installer les dépendances:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Remarque: si `pip install` échoue pour cause de certificat TLS (chemin CA invalide), vous pouvez temporairement exécuter:

```powershell
python -m pip install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org
```

3) Charger les fichiers Excel dans la base (loader moderne)

Le loader principal est `scripts/load_data.py`. Il lit les fichiers sous le dossier `db/` et charge:
- `db/IDS_2026.xlsx` -> schema `cholera.cas_maladie`
- `db/rdc_compilation*_LL_Cholera_*.xlsx` -> schema `cholera.cas_ll`

Exécution:

```powershell
python scripts/load_data.py
```

Le script journalise les actions dans la console (niveau INFO). Si vous avez besoin d’un import contrôlé, restaurez/renommez les fichiers dans `db/` avant d’exécuter.

4) Préparer et appliquer les corrections (normalisation des valeurs)

Le fichier de mapping complet se trouve dans `data/replace_values.xlsx` (feuille `valeurs`). Il contient des règles (regex) pour normaliser des champs comme `Issue`, `tdr_resultat`, `sexe`, etc.

- Dry-run (simulation) — liste les remplacements et compte les lignes affectées:

```powershell
python scripts/apply_corrections.py
```

- Appliquer les changements en base:

```powershell
python scripts/apply_corrections.py --apply
```

Chaque exécution écrit un log CSV dans le dossier `logs/` nommé `corrections_YYYYMMDD_HHMMSS.csv` contenant: table, colonne, pattern, remplacement, affected.

5) Vérifier l’état des données (checks rapides)

Un utilitaire simple est fourni: `scripts/check_data.py`. Il exécute quelques contrôles (comptes, clés nulles, duplications simples) et écrit un rapport dans `logs/check_data_YYYYMMDD_HHMMSS.txt`.

```powershell
python scripts/check_data.py
```

6) Sauvegarde / rollback

- Avant d’appliquer des corrections en production, faites une sauvegarde complète:

```powershell
pg_dump -h localhost -p 5432 -U bearing -d ids_db -F c -f backup_ids_db_YYYYMMDD.dump
```

- Pour restaurer (attention: écrase la base):

```powershell
pg_restore -h localhost -p 5432 -U bearing -d ids_db --clean backup_ids_db_YYYYMMDD.dump
```

7) Bonnes pratiques

- Toujours lancer `python scripts/apply_corrections.py` sans `--apply` d’abord (dry-run).
- Vérifier le CSV de log dans `logs/` et le rapport `scripts/check_data.py` après application.
- Versionner `data/replace_values.xlsx` si vous modifiez les règles.
- Ajouter des tests ou règles supplémentaires dans `data/replace_values.xlsx` puis retester en dry-run.

8) Débogage et support

- Si `pip` se plaint d’un CA bundle invalide, utilisez l’option `--trusted-host` ou corrigez le `pip.ini`.
- Les scripts utilisent la variable d’environnement `POSTGRES_*` si vous souhaitez pointer vers une autre base.
- Logs et rapports: tout est écrit dans le dossier `logs/`.

Fichiers utiles
- `scripts/load_data.py` — loader moderne Excel → Postgres
- `scripts/apply_corrections.py` — applique les corrections définies dans `data/replace_values.xlsx` (dry-run + --apply)
- `scripts/check_data.py` — vérifications rapides post-import / post-corrections
- `data/replace_values.xlsx` — table de correspondances / regex

Besoin d’automatiser davantage (CI, tests, validations métier) ? Dites-moi ce que vous voulez automatiser en priorité et je peux ajouter des tests SQL/pytest + pipeline CI.
