#!/usr/bin/env python3
"""
Script de test pour le serveur Flask Fresheo Delivery Labels
"""

import requests
import sys
import json
from datetime import datetime

def test_server(base_url="http://localhost:5000"):
    """Test les différents endpoints du serveur"""
    
    print(f"🧪 Test du serveur Fresheo Labels sur {base_url}")
    print("=" * 60)
    
    # Test 1: Health check
    print("1️⃣ Test health check...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"   ✅ Serveur en ligne")
            print(f"   📅 Dates cibles: {health_data['target_dates']}")
            print(f"   🕐 Timestamp: {health_data['timestamp']}")
        else:
            print(f"   ❌ Health check échoué: {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"   ❌ Erreur de connexion: {e}")
        return False
    
    print()
    
    # Test 2: Page d'accueil
    print("2️⃣ Test page d'accueil...")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print(f"   ✅ Page d'accueil accessible")
            print(f"   📄 Taille: {len(response.text)} caractères")
        else:
            print(f"   ❌ Page d'accueil échouée: {response.status_code}")
    except requests.RequestException as e:
        print(f"   ❌ Erreur page d'accueil: {e}")
    
    print()
    
    # Test 3: CSV endpoint (test de structure seulement)
    print("3️⃣ Test endpoint CSV...")
    try:
        response = requests.get(f"{base_url}/delivery.csv", timeout=30)
        
        if response.status_code == 200:
            print(f"   ✅ CSV généré avec succès")
            print(f"   📄 Taille: {len(response.text)} caractères")
            
            # Analyser les premières lignes
            lines = response.text.split('\n')
            if len(lines) > 0:
                print(f"   📋 Header: {lines[0]}")
                print(f"   📊 Nombre de lignes: {len([l for l in lines if l.strip()])}")
                
                # Vérifier les colonnes attendues
                expected_columns = [
                    'order_id', 'shipping_group', 'shipping_order', 'qrcode_data',
                    'total_meals', 'max_meals', 'labels_quantity', 'shipping_date',
                    'color', 'user_lang', 'cust_name', 'shipping_label', 'delivery_status'
                ]
                
                if lines[0]:
                    actual_columns = [col.strip() for col in lines[0].split(',')]
                    missing_columns = set(expected_columns) - set(actual_columns)
                    extra_columns = set(actual_columns) - set(expected_columns)
                    
                    if not missing_columns and not extra_columns:
                        print(f"   ✅ Structure CSV correcte ({len(actual_columns)} colonnes)")
                    else:
                        if missing_columns:
                            print(f"   ⚠️  Colonnes manquantes: {missing_columns}")
                        if extra_columns:
                            print(f"   ⚠️  Colonnes supplémentaires: {extra_columns}")
                
                # Afficher un exemple de ligne de données si disponible
                if len(lines) > 1 and lines[1].strip():
                    print(f"   📝 Exemple de ligne: {lines[1][:100]}...")
            
        elif response.status_code == 500:
            try:
                error_data = response.json()
                print(f"   ❌ Erreur serveur: {error_data.get('error', 'Erreur inconnue')}")
                
                if 'Token API manquant' in str(error_data):
                    print(f"   💡 Solution: Créer fichier .env avec FRESHEO_API_TOKEN=votre_token")
            except:
                print(f"   ❌ Erreur serveur: {response.status_code}")
        else:
            print(f"   ❌ CSV échoué: {response.status_code}")
            print(f"   📄 Réponse: {response.text[:200]}...")
            
    except requests.RequestException as e:
        print(f"   ❌ Erreur CSV: {e}")
    
    print()
    print("=" * 60)
    print("🏁 Tests terminés")
    
    return True

def main():
    """Point d'entrée principal"""
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    
    print(f"🚀 Test du serveur Flask Fresheo Labels")
    print(f"📍 URL de test: {base_url}")
    print()
    
    # Afficher les instructions si le serveur n'est pas accessible
    try:
        requests.get(f"{base_url}/health", timeout=2)
    except requests.RequestException:
        print("⚠️  Le serveur ne semble pas accessible.")
        print("📋 Instructions pour démarrer:")
        print("   1. Créer fichier .env avec FRESHEO_API_TOKEN=votre_token")
        print("   2. python app.py")
        print("   3. python test_server.py")
        print()
        return
    
    test_server(base_url)

if __name__ == "__main__":
    main() 