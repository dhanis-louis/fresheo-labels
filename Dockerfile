FROM python:3.11-slim

# Variables d'environnement pour optimiser Python en production
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Créer un utilisateur non-root pour la sécurité
RUN useradd --create-home --shell /bin/bash app

# Répertoire de travail
WORKDIR /app

# Copier les requirements et installer les dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code de l'application
COPY app.py .
COPY README.md .

# Changer le propriétaire des fichiers
RUN chown -R app:app /app

# Changer vers l'utilisateur non-root
USER app

# Exposer le port
EXPOSE 5001

# Healthcheck pour Docker
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5001/health', timeout=10)"

# Commande de démarrage avec gunicorn pour la production
CMD ["python", "-m", "gunicorn", "--bind", "0.0.0.0:5001", "--timeout", "600", "--workers", "2", "--worker-class", "sync", "--max-requests", "100", "--max-requests-jitter", "10", "app:app"] 