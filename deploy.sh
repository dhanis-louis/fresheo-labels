#!/bin/bash

# 🚀 Script de déploiement DigitalOcean - Fresheo Labels API
# Usage: ./deploy.sh

set -e  # Arrêt en cas d'erreur

echo "🚀 Déploiement Fresheo Labels API sur DigitalOcean"
echo "=================================================="

# Vérifications préalables
echo "📋 Vérifications préalables..."

if [ ! -f ".env" ]; then
    echo "❌ Fichier .env manquant!"
    echo "💡 Créez le fichier .env basé sur env.production"
    echo "   cp env.production .env"
    echo "   # Puis éditez .env avec vos vraies valeurs"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "❌ Docker n'est pas installé!"
    echo "💡 Installez Docker: https://docs.docker.com/install/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose n'est pas installé!"
    echo "💡 Installez Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# Vérifier que le token API est configuré
if grep -q "your_production_token_here" .env; then
    echo "❌ Token API non configuré dans .env!"
    echo "💡 Éditez le fichier .env et remplacez 'your_production_token_here' par votre vrai token"
    exit 1
fi

echo "✅ Vérifications OK"

# Créer les répertoires nécessaires
echo "📁 Création des répertoires..."
mkdir -p logs
mkdir -p ssl

echo "✅ Répertoires créés"

# Arrêter les conteneurs existants
echo "🛑 Arrêt des conteneurs existants..."
docker-compose down --remove-orphans || true

# Construire l'image
echo "🏗️  Construction de l'image Docker..."
docker-compose build --no-cache

# Démarrer les services
echo "🚀 Démarrage des services..."
docker-compose up -d

# Attendre que les services soient prêts
echo "⏳ Attente du démarrage des services..."
sleep 10

# Test de santé
echo "🩺 Test de santé..."
for i in {1..12}; do
    if curl -f http://localhost/health > /dev/null 2>&1; then
        echo "✅ Service démarré avec succès!"
        break
    else
        echo "⏳ Tentative $i/12 - Service en cours de démarrage..."
        sleep 5
    fi
    
    if [ $i -eq 12 ]; then
        echo "❌ Échec du démarrage du service!"
        echo "📋 Logs de l'application:"
        docker-compose logs app
        exit 1
    fi
done

# Afficher les informations de déploiement
echo ""
echo "🎉 Déploiement réussi!"
echo "======================"
echo ""
echo "📍 URLs disponibles:"
echo "   🏠 Page d'accueil: http://your-server-ip/"
echo "   ❤️  Health check:  http://your-server-ip/health"
echo "   📥 CSV principal:  http://your-server-ip/delivery.csv"
echo ""
echo "🧪 URLs de test:"
echo "   🚚 Test tournées:  http://your-server-ip/test/rounds"
echo "   📦 Test commande:  http://your-server-ip/test/order/12345"
echo ""
echo "🎯 Simulation de jour:"
echo "   📅 Vendredi:       http://your-server-ip/delivery.csv?today=2025-08-01"
echo "   📅 Samedi:         http://your-server-ip/delivery.csv?today=2025-08-02"
echo ""
echo "📊 Monitoring:"
echo "   📋 Status:         docker-compose ps"
echo "   📜 Logs app:       docker-compose logs -f app"
echo "   📜 Logs nginx:     docker-compose logs -f nginx"
echo ""
echo "🔧 Gestion:"
echo "   🛑 Arrêter:        docker-compose down"
echo "   🔄 Redémarrer:     docker-compose restart"
echo "   🆙 Mise à jour:    git pull && ./deploy.sh"
echo ""
echo "⚠️  IMPORTANT:"
echo "   • Les timeouts sont configurés pour 10 minutes maximum"
echo "   • Rate limiting: 5 requêtes CSV par minute par IP"
echo "   • Logs dans ./logs/"
echo ""
echo "✅ Déploiement terminé avec succès!" 