# ================================
#  Dockerfile - cholera-pipeline
# ================================

# Étape 1 : Base Python légère
FROM python:3.9-slim

# Mainteneur
LABEL maintainer="bearing.kalela@cousp.org"
LABEL description="Pipeline de traitement et d'analyse des données Cholera"

# Définition du répertoire de travail
WORKDIR /app

# Copie du dossier scripts (contenant 00_main.py, imports, utils, etc.)
COPY ./scripts /app/scripts

# Copie du dossier dataminsante (lib interne)
COPY ./dataminsante /app/dataminsante

# Copie des données d’entrée (CSV/Excel) et du dossier db
COPY ./data /app/data
COPY ./db/data /app/db_data

# Installation des dépendances Python
# Utilise requirements.txt présent dans scripts/
RUN pip install --no-cache-dir --root-user-action=ignore -r /app/scripts/requirements.txt


# Variables d’environnement Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Ajout de /app et /app/scripts dans le PYTHONPATH pour les imports internes
ENV PYTHONPATH="/app:/app/scripts"

# Commande par défaut : exécuter le pipeline
CMD ["python", "-m", "scripts.main"]
