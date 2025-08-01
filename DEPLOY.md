# 🚀 Guide de déploiement DigitalOcean - Fresheo Labels API

Ce guide vous accompagne pour déployer l'API d'étiquettes Fresheo sur DigitalOcean avec gestion des timeouts longs (5+ minutes).

## 📋 Prérequis

### 🖥️ Serveur DigitalOcean

- **Instance recommandée** : Droplet 2GB RAM minimum (car les requêtes API sont lourdes)
- **OS** : Ubuntu 22.04 LTS
- **Ports** : 80 (HTTP), 443 (HTTPS optionnel), 22 (SSH)

### 🔧 Logiciels requis

- Docker & Docker Compose
- Git
- Curl (pour les tests)

## 🏁 Déploiement rapide

### Étape 1: Connexion au serveur

```bash
ssh root@your-server-ip
```

### Étape 2: Installation des dépendances

```bash
# Mise à jour du système
apt update && apt upgrade -y

# Installation Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Installation Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Vérifications
docker --version
docker-compose --version
```

### Étape 3: Récupération du code

```bash
# Cloner le repository (adaptez l'URL)
git clone https://github.com/your-repo/fresheo-labels.git
cd fresheo-labels

# Ou uploadez les fichiers via SCP si pas de Git
```

### Étape 4: Configuration

```bash
# Copier le template de configuration
cp env.production .env

# Éditer la configuration avec vos vraies valeurs
nano .env
```

**Important** : Remplacez dans `.env` :

```bash
FRESHEO_API_TOKEN=your_real_token_here
FRESHEO_BASE_URL=https://api.fresheo.be
```

### Étape 5: Déploiement

```bash
# Rendre le script exécutable
chmod +x deploy.sh

# Lancer le déploiement
./deploy.sh
```

### Étape 6: Test

```bash
# Test de santé
curl http://your-server-ip/health

# Test CSV (peut prendre plusieurs minutes!)
curl -o test.csv "http://your-server-ip/delivery.csv"
```

## ⚙️ Configuration avancée

### 🕐 Gestion des timeouts

Le système est configuré pour gérer des requêtes très longues :

| Composant    | Timeout      | Usage              |
| ------------ | ------------ | ------------------ |
| **Nginx**    | 600s (10min) | Proxy vers l'app   |
| **Gunicorn** | 600s (10min) | Serveur WSGI       |
| **Requests** | 600s (10min) | Appels API Fresheo |
| **Docker**   | Illimité     | Healthcheck        |

### 📊 Monitoring et logs

```bash
# Status des conteneurs
docker-compose ps

# Logs en temps réel
docker-compose logs -f app
docker-compose logs -f nginx

# Logs spécifiques
tail -f logs/app.log
tail -f /var/log/nginx/fresheo-labels.log
```

### 🔒 Sécurité

- **Rate limiting** : 5 requêtes CSV/minute/IP
- **Headers sécurisé** : CSP, XSS protection, etc.
- **Utilisateur non-root** dans les conteneurs
- **Isolation réseau** Docker

## 🎯 URLs de production

Une fois déployé, vos URLs seront :

### 📍 URLs principales

- **Page d'accueil** : `http://your-server-ip/`
- **Health check** : `http://your-server-ip/health`
- **CSV automatique** : `http://your-server-ip/delivery.csv`

### 🧪 URLs de test

- **Test tournées** : `http://your-server-ip/test/rounds`
- **Test commande** : `http://your-server-ip/test/order/12345`

### 🎲 Simulation de jour

- **Vendredi** : `http://your-server-ip/delivery.csv?today=2025-08-01`
- **Samedi** : `http://your-server-ip/delivery.csv?today=2025-08-02`
- **Date forcée** : `http://your-server-ip/delivery.csv?date=2025-08-10`

## 🔧 Maintenance

### 🔄 Mise à jour

```bash
cd fresheo-labels
git pull
./deploy.sh
```

### 🛑 Arrêt

```bash
docker-compose down
```

### 🚀 Redémarrage

```bash
docker-compose restart
```

### 🧹 Nettoyage

```bash
# Supprimer les anciennes images
docker system prune -a

# Nettoyer les logs
truncate -s 0 logs/*.log
```

## 🚨 Dépannage

### ❌ Timeout lors du CSV

```bash
# Vérifier les logs
docker-compose logs app | grep ERROR

# Augmenter les timeouts si nécessaire (dans nginx.conf)
proxy_read_timeout 900s;  # 15 minutes
```

### 🐌 Performance lente

```bash
# Vérifier les ressources
htop
docker stats

# Augmenter la RAM du Droplet si nécessaire
# (minimum 2GB recommandé)
```

### 🔗 Erreur de connexion API

```bash
# Tester la connectivité
curl -v https://api.fresheo.be/api/bo/v1/rounds/delivery?date=2025-08-01

# Vérifier le token
grep FRESHEO_API_TOKEN .env
```

### 📊 Logs détaillés

```bash
# Activer le debug temporairement
echo "DEBUG=True" >> .env
docker-compose restart app

# Remettre en production
sed -i 's/DEBUG=True/DEBUG=False/' .env
docker-compose restart app
```

## 📈 Optimisations production

### 🚀 Performance

- Utilisez un Droplet avec SSD
- Activez le swap si besoin
- Considérez un CDN pour les assets statiques

### 🔒 HTTPS (optionnel)

```bash
# Avec Let's Encrypt
apt install certbot
certbot --nginx -d your-domain.com

# Puis modifiez nginx.conf pour inclure SSL
```

### 📊 Monitoring externe

Configurez un monitoring externe qui appelle :

- `http://your-server-ip/health` (toutes les 5 minutes)
- Alerte si timeout > 30 secondes

## ✅ Checklist de déploiement

- [ ] Serveur DigitalOcean avec 2GB+ RAM
- [ ] Docker et Docker Compose installés
- [ ] Code récupéré sur le serveur
- [ ] Fichier `.env` configuré avec vrai token
- [ ] Script `deploy.sh` exécuté avec succès
- [ ] Health check répond : `curl http://ip/health`
- [ ] CSV se génère : `curl -o test.csv http://ip/delivery.csv`
- [ ] Logs configurés et accessibles
- [ ] Monitoring externe configuré (optionnel)

---

**🎉 Votre API Fresheo Labels est maintenant déployée et prête à gérer des requêtes longues !**

Pour toute question : vérifiez les logs avec `docker-compose logs -f app`
