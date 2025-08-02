import os
import csv
import io
import math
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from flask import Flask, Response, jsonify, request
import logging
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

class FresheoDeliveryAPI:
    def __init__(self, base_url: str, token: str):
        # S'assurer que l'URL de base contient /api/bo/v1
        base_url = base_url.rstrip('/')
        if not base_url.endswith('/api/bo/v1'):
            base_url = base_url + '/api/bo/v1'
        
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

    def get_delivery_rounds_for_date(self, date: str) -> List[Dict[str, Any]]:
        """Récupère toutes les tournées pour une date donnée"""
        url = f"{self.base_url}/rounds/delivery"
        params = {'date': date}
        
        try:
            # Timeout long pour éviter les problèmes de performance (5+ minutes parfois)
            response = requests.get(url, headers=self.headers, params=params, timeout=600)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            app.logger.error(f"Erreur lors de la récupération des tournées: {e}")
            raise

    def get_round_details(self, round_id: int) -> Dict[str, Any]:
        """Récupère les détails d'une tournée spécifique"""
        url = f"{self.base_url}/rounds/delivery/{round_id}"
        
        try:
            # Timeout long pour les détails de tournée qui peuvent être volumineux
            response = requests.get(url, headers=self.headers, timeout=300)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            app.logger.warning(f"Impossible de récupérer les détails de la tournée {round_id}: {e}")
            return {}

    def get_order_details(self, order_id: int) -> Dict[str, Any]:
        """Récupère les détails complets d'une commande"""
        url = f"{self.base_url}/get-order/{order_id}/delivery"
        
        try:
            # Timeout augmenté pour les détails de commande
            response = requests.get(url, headers=self.headers, timeout=120)
            response.raise_for_status()
            data = response.json()
            
            # L'API peut retourner un array ou un objet
            if isinstance(data, list):
                if len(data) > 0:
                    return data[0]  # Retourner le premier élément
                else:
                    app.logger.warning(f"API a retourné une liste vide pour la commande {order_id}")
                    return {}  # Retourner un dict vide si liste vide
            else:
                return data  # Si c'est déjà un dict, retourner tel quel
        except requests.exceptions.RequestException as e:
            app.logger.warning(f"Impossible de récupérer les détails de la commande {order_id}: {e}")
            return {}

def get_target_date(simulated_today: datetime = None) -> str:
    """
    Reproduit la logique SQL de filtrage par date selon le jour de la semaine
    Note: Retourne la première date de la plage pour la nouvelle API
    """
    today = simulated_today if simulated_today else datetime.now()
    day_of_week = today.weekday()  # 0=Lundi, 4=Vendredi, 5=Samedi, 6=Dimanche
    
    if day_of_week == 4:  # Vendredi → Samedi
        return (today + timedelta(days=1)).strftime("%Y-%m-%d")
    elif day_of_week == 5:  # Samedi → Dimanche (première date de la plage dim-mar)
        return (today + timedelta(days=1)).strftime("%Y-%m-%d")
    else:  # Autres jours → Aujourd'hui
        return today.strftime("%Y-%m-%d")

def get_target_dates_range(simulated_today: datetime = None) -> List[str]:
    """
    Retourne toutes les dates cibles selon la logique SQL EXACTE
    SQL: WHEN 6 THEN shipping_date BETWEEN CURRENT_DATE + INTERVAL '1 day' AND CURRENT_DATE + INTERVAL '3 days'
    """
    today = simulated_today if simulated_today else datetime.now()
    day_of_week = today.weekday()  # 0=Lundi, 4=Vendredi, 5=Samedi, 6=Dimanche
    
    if day_of_week == 4:  # Vendredi → Samedi (CURRENT_DATE + 1 day)
        target_date = (today + timedelta(days=1)).strftime("%Y-%m-%d")
        return [target_date]
    elif day_of_week == 5:  # Samedi → Dimanche à Mardi (BETWEEN +1 day AND +3 days)
        dates = []
        dates.append((today + timedelta(days=1)).strftime("%Y-%m-%d"))  # Dimanche (+1)
        dates.append((today + timedelta(days=2)).strftime("%Y-%m-%d"))  # Lundi (+2)
        dates.append((today + timedelta(days=3)).strftime("%Y-%m-%d"))  # Mardi (+3)
        return dates
    else:  # Autres jours → Aujourd'hui (CURRENT_DATE)
        return [today.strftime("%Y-%m-%d")]

def get_day_name_french(date_str: str) -> str:
    """Convertit une date en nom de jour en français"""
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    days = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche']
    return days[date_obj.weekday()]

def get_delivery_planning_name(date_str: str, time_slot: str) -> str:
    """
    Génère le delivery_planning_name au format "lundi matin" ou "mardi soir"
    """
    day_name = get_day_name_french(date_str)
    
    # Extraire l'heure du time_slot (format "09:00" ou "13:00")
    try:
        hour = int(time_slot.split(':')[0])
        period = "matin" if hour < 12 else "soir"
        return f"{day_name} {period}"
    except (ValueError, IndexError):
        return f"{day_name} journée"

def format_customer_name(first_name: str, last_name: str) -> str:
    """Formate le nom client en Title Case comme dans SQL INITCAP"""
    return f"{first_name.title()} {last_name.title()}"

def calculate_labels_quantity(total_meals: int) -> int:
    """Calcule le nombre d'étiquettes nécessaires (ceil(total_meals / 7))"""
    return math.ceil(total_meals / 7)

def generate_color_code(delivery_tour_index: int) -> str:
    """Génère le code couleur basé sur l'index de tournée"""
    return f"color_{((delivery_tour_index % 10) + 1)}"

def extract_orders_for_csv(date: str, api: FresheoDeliveryAPI) -> List[Dict[str, Any]]:
    """
    Extrait et formate toutes les commandes pour le CSV en utilisant la nouvelle API
    """
    orders_for_csv = []
    
    # 1. Récupérer toutes les tournées du jour
    rounds = api.get_delivery_rounds_for_date(date)
    app.logger.info(f"Récupération tournées pour {date}: type={type(rounds)}, count={len(rounds) if isinstance(rounds, list) else 'NOT_LIST'}")
    
    # Vérification de sécurité: rounds doit être une liste
    if not isinstance(rounds, list):
        app.logger.error(f"get_delivery_rounds_for_date a retourné un {type(rounds)} au lieu d'une liste: {rounds}")
        return []
    
    # 2. Pour chaque tournée, récupérer les détails
    for round_data in rounds:
        # Vérification de sécurité: round_data doit être un dict
        if not isinstance(round_data, dict) or 'id' not in round_data:
            app.logger.error(f"round_data invalide: {type(round_data)} = {round_data}")
            continue
            
        round_details = api.get_round_details(round_data['id'])
        app.logger.info(f"Tournée {round_data['id']}: type={type(round_details)}, keys={list(round_details.keys()) if isinstance(round_details, dict) else 'NOT_DICT'}")
        
        # 3. Extraire les commandes de cette tournée
        if not isinstance(round_details, dict):
            app.logger.error(f"round_details n'est pas un dict: {type(round_details)} = {round_details}")
            continue
            
        orders = round_details.get('orders', [])
        if not isinstance(orders, list):
            app.logger.error(f"orders n'est pas une liste: {type(orders)} = {orders}")
            continue
            
        for order in orders:
            # Récupérer les détails complets de la commande pour total_meals
            order_details = api.get_order_details(order['id'])
            total_meals = order_details.get('total_meals', 4)  # Valeur par défaut si non trouvé
            
            # Construire l'enregistrement CSV
            csv_record = {
                'order_id': order['id'],
                'shipping_group': round_data['round'],  # Numéro de tournée
                'shipping_order': order['index'],  # Position dans la tournée
                'qrcode_data': f"BE_{order['id']}",
                'total_meals': total_meals,
                'max_meals': total_meals,  # Égal à total_meals comme suggéré
                'labels_quantity': calculate_labels_quantity(total_meals),
                'shipping_date': date,
                'color': generate_color_code(round_data['round']),
                'user_lang': 'FR',  # Fixe comme suggéré
                'cust_name': order['customerName'],  # Disponible directement
                'shipping_label': get_delivery_planning_name(date, round_data['timeOfDay']),
                'delivery_status': order['deliveryStatus'] == 'replacement' if order['deliveryStatus'] else False
            }
            
            orders_for_csv.append(csv_record)
    
    # Trier comme dans la requête SQL
    orders_for_csv.sort(key=lambda x: (
        x['shipping_date'],
        x['shipping_label'],
        x['shipping_group'],
        x['shipping_order']
    ))
    
    return orders_for_csv

@app.route('/delivery.csv')
def delivery_csv():
    """
    Endpoint principal qui retourne le CSV des livraisons
    Paramètre optionnel: ?date=yyyy-mm-dd pour spécifier une date de test
    """
    try:
        # Configuration API depuis le fichier .env
        base_url_raw = os.getenv('FRESHEO_BASE_URL', 'https://api.fresheo.be')
        token = os.getenv('FRESHEO_API_TOKEN', 'your_default_token_here')
        
        # S'assurer que l'URL de base contient /api/bo/v1
        base_url = base_url_raw.rstrip('/')
        if not base_url.endswith('/api/bo/v1'):
            base_url = base_url + '/api/bo/v1'
        
        if not token or token == 'your_default_token_here':
            return jsonify({'error': 'Token API manquant. Configurer FRESHEO_API_TOKEN dans .env'}), 500
        
        # Initialiser l'API
        api = FresheoDeliveryAPI(base_url, token)
        
        # Vérifier les paramètres de test
        test_date = request.args.get('date')      # Force une date de livraison spécifique
        simulate_today = request.args.get('today') # Simule "quel jour on est"
        
        if test_date and simulate_today:
            return jsonify({'error': 'Utiliser soit date= soit today=, pas les deux'}), 400
        
        if test_date:
            # Mode 1: Date de livraison forcée
            try:
                datetime.strptime(test_date, '%Y-%m-%d')
                target_dates = [test_date]
                app.logger.info(f"🎯 Mode date forcée: livraisons pour {test_date}")
            except ValueError:
                return jsonify({'error': 'Format de date invalide. Utiliser yyyy-mm-dd'}), 400
                
        elif simulate_today:
            # Mode 2: Simulation du jour actuel + logique SQL
            try:
                simulated_today_dt = datetime.strptime(simulate_today, '%Y-%m-%d')
                target_dates = get_target_dates_range(simulated_today_dt)
                day_names = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche']
                day_name = day_names[simulated_today_dt.weekday()]
                app.logger.info(f"🧪 Mode simulation: comme si on était {day_name} {simulate_today}")
                app.logger.info(f"📅 → Livraisons pour: {target_dates}")
            except ValueError:
                return jsonify({'error': 'Format de date invalide pour today. Utiliser yyyy-mm-dd'}), 400
                
        else:
            # Mode 3: Logique SQL normale (vraie date actuelle)
            target_dates = get_target_dates_range()
            real_today = datetime.now().strftime('%Y-%m-%d')
            day_names = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche']
            day_name = day_names[datetime.now().weekday()]
            app.logger.info(f"📅 Mode automatique: vraiment {day_name} {real_today}")
            app.logger.info(f"📅 → Livraisons pour: {target_dates}")
        
        all_orders_for_csv = []
        
        # Pour chaque date cible, récupérer les commandes
        for date in target_dates:
            try:
                app.logger.info(f"Traitement de la date: {date}")
                orders_for_date = extract_orders_for_csv(date, api)
                all_orders_for_csv.extend(orders_for_date)
            except Exception as e:
                import traceback
                app.logger.error(f"Erreur pour la date {date}: {e}")
                app.logger.error(f"Traceback complet: {traceback.format_exc()}")
                # Retourner l'erreur pour débugger au lieu de continuer silencieusement
                raise
        
        app.logger.info(f"Génération du CSV pour {len(all_orders_for_csv)} commandes")
        
        # Générer le CSV
        output = io.StringIO()
        fieldnames = [
            'order_id', 'shipping_group', 'shipping_order', 'qrcode_data',
            'total_meals', 'max_meals', 'labels_quantity', 'shipping_date',
            'color', 'user_lang', 'cust_name', 'shipping_label', 'delivery_status'
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_orders_for_csv)
        
        # Retourner la réponse CSV
        filename_dates = "_".join(target_dates)
        
        # Suffix selon le mode utilisé
        if test_date:
            mode_suffix = "_date_forced"
        elif simulate_today:
            mode_suffix = f"_simulated_{simulate_today}"
        else:
            mode_suffix = "_auto"
            
        response = Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=delivery_labels_{filename_dates}{mode_suffix}.csv'
            }
        )
        
        return response
        
    except Exception as e:
        app.logger.error(f"Erreur lors de la génération du CSV: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    """Endpoint de vérification de santé"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'current_day': datetime.now().strftime('%A'),
        'target_date': get_target_date(),
        'target_dates_range': get_target_dates_range(),
        'simulation_examples': {
            'friday': get_target_dates_range(datetime(2025, 8, 1)),   # vendredi → samedi
            'saturday': get_target_dates_range(datetime(2025, 8, 2)), # samedi → dim+lun+mar 
            'monday': get_target_dates_range(datetime(2025, 8, 4))    # lundi → lundi
        }
    })

@app.route('/test/order/<int:order_id>')
def test_order(order_id):
    """Endpoint de test pour récupérer une commande spécifique"""
    try:
        # Configuration API depuis le fichier .env
        base_url_raw = os.getenv('FRESHEO_BASE_URL', 'https://api.fresheo.be')
        token = os.getenv('FRESHEO_API_TOKEN', 'your_default_token_here')
        
        # S'assurer que l'URL de base contient /api/bo/v1
        base_url = base_url_raw.rstrip('/')
        if not base_url.endswith('/api/bo/v1'):
            base_url = base_url + '/api/bo/v1'
        
        if not token or token == 'your_default_token_here':
            return jsonify({'error': 'Token API manquant. Configurer FRESHEO_API_TOKEN dans .env'}), 500
        
        # Initialiser l'API
        api = FresheoDeliveryAPI(base_url, token)
        
        app.logger.info(f"Test récupération commande {order_id}")
        
        # Récupérer les détails de la commande
        order_details = api.get_order_details(order_id)
        
        if not order_details:
            return jsonify({'error': f'Commande {order_id} non trouvée ou inaccessible'}), 404
        
        return jsonify({
            'order_id': order_id,
            'url_called': f"{base_url}/get-order/{order_id}/delivery",
            'data': order_details,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        app.logger.error(f"Erreur lors du test de la commande {order_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/test/rounds')
@app.route('/test/deliveries')  # Alias pour compatibilité
def test_rounds():
    """Endpoint de test pour récupérer les tournées de livraison"""
    try:
        # Configuration API depuis le fichier .env
        base_url_raw = os.getenv('FRESHEO_BASE_URL', 'https://api.fresheo.be')
        token = os.getenv('FRESHEO_API_TOKEN', 'your_default_token_here')
        
        if not token or token == 'your_default_token_here':
            return jsonify({'error': 'Token API manquant. Configurer FRESHEO_API_TOKEN dans .env'}), 500
        
        # S'assurer que l'URL de base contient /api/bo/v1
        base_url = base_url_raw.rstrip('/')
        if not base_url.endswith('/api/bo/v1'):
            base_url = base_url + '/api/bo/v1'
        
        # Calculer la date cible selon la logique SQL
        target_date = get_target_date()
        app.logger.info(f"Test récupération tournées pour {target_date}")
        
        # Test direct avec requests pour debugging
        url = f"{base_url}/rounds/delivery"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        params = {'date': target_date}
        
        try:
            # Timeout long pour les tests - peut prendre plusieurs minutes
            response = requests.get(url, headers=headers, params=params, timeout=600)
            app.logger.info(f"Response status: {response.status_code}")
            app.logger.info(f"Response headers: {dict(response.headers)}")
            
            if response.status_code == 500:
                app.logger.error(f"Response text: {response.text[:500]}")
                return jsonify({
                    'error': 'Erreur 500 du serveur backend',
                    'url_called': url,
                    'target_date': target_date,
                    'params': params,
                    'status_code': response.status_code,
                    'response_text': response.text[:500],
                    'timestamp': datetime.now().isoformat()
                }), 500
            
            response.raise_for_status()
            rounds_data = response.json()
            
            return jsonify({
                'success': True,
                'url_called': url,
                'target_date': target_date,
                'params': params,
                'rounds_count': len(rounds_data) if isinstance(rounds_data, list) else 0,
                'data': rounds_data,
                'timestamp': datetime.now().isoformat()
            })
            
        except requests.exceptions.RequestException as e:
            app.logger.error(f"Erreur requête: {e}")
            return jsonify({
                'error': str(e),
                'url_called': url,
                'target_date': target_date,
                'params': params,
                'timestamp': datetime.now().isoformat()
            }), 500
        
    except Exception as e:
        app.logger.error(f"Erreur lors du test des tournées: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/test/round/<int:round_id>')
def test_round_details(round_id):
    """Endpoint de test pour récupérer les détails d'une tournée spécifique"""
    try:
        # Configuration API depuis le fichier .env
        base_url_raw = os.getenv('FRESHEO_BASE_URL', 'https://api.fresheo.be')
        token = os.getenv('FRESHEO_API_TOKEN', 'your_default_token_here')
        
        # S'assurer que l'URL de base contient /api/bo/v1
        base_url = base_url_raw.rstrip('/')
        if not base_url.endswith('/api/bo/v1'):
            base_url = base_url + '/api/bo/v1'
        
        if not token or token == 'your_default_token_here':
            return jsonify({'error': 'Token API manquant. Configurer FRESHEO_API_TOKEN dans .env'}), 500
        
        # Initialiser l'API
        api = FresheoDeliveryAPI(base_url, token)
        
        app.logger.info(f"Test récupération détails tournée {round_id}")
        
        # Récupérer les détails de la tournée
        round_details = api.get_round_details(round_id)
        
        if not round_details:
            return jsonify({'error': f'Tournée {round_id} non trouvée ou inaccessible'}), 404
        
        return jsonify({
            'round_id': round_id,
            'url_called': f"{base_url}/rounds/delivery/{round_id}",
            'orders_count': len(round_details.get('orders', [])),
            'data': round_details,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        app.logger.error(f"Erreur lors du test de la tournée {round_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    """Page d'accueil avec instructions"""
    return """
    <h1>🏷️ Fresheo Delivery Labels API - Version 2.3</h1>
    <h2>✨ Endpoints principaux :</h2>
    <ul>
        <li><a href="/delivery.csv"><strong>/delivery.csv</strong></a> - 📅 <strong>CSV automatique</strong> (logique SQL réelle)</li>
        <li><a href="/health">/health</a> - ❤️ Vérification de santé</li>
    </ul>
    
    <h2>🧪 Modes de test :</h2>
    
    <h3>🎯 Mode 1: Simulation du jour actuel</h3>
    <p><strong>Paramètre:</strong> <code>today=yyyy-mm-dd</code> - Simule "quel jour on est" et applique la logique SQL</p>
    <ul>
        <li><a href="/delivery.csv?today=2025-08-01"><code>/delivery.csv?today=2025-08-01</code></a> - Comme si on était vendredi → étiquettes samedi</li>
        <li><a href="/delivery.csv?today=2025-08-02"><code>/delivery.csv?today=2025-08-02</code></a> - Comme si on était samedi → étiquettes dim+lun+mar</li>
        <li><a href="/delivery.csv?today=2025-08-04"><code>/delivery.csv?today=2025-08-04</code></a> - Comme si on était lundi → étiquettes lundi</li>
    </ul>
    
    <h3>🎯 Mode 2: Date de livraison forcée</h3>
    <p><strong>Paramètre:</strong> <code>date=yyyy-mm-dd</code> - Force les étiquettes d'une date spécifique</p>
    <ul>
        <li><a href="/delivery.csv?date=2025-08-05"><code>/delivery.csv?date=2025-08-05</code></a> - Étiquettes du 5 août uniquement</li>
        <li><a href="/delivery.csv?date=2025-08-10"><code>/delivery.csv?date=2025-08-10</code></a> - Étiquettes du 10 août uniquement</li>
    </ul>
    
    <h2>🔬 Logique SQL :</h2>
    <div style="background: #f5f5f5; padding: 10px; border-left: 4px solid #007acc;">
    <strong>Vendredi</strong> → Étiquettes du samedi<br/>
    <strong>Samedi</strong> → Étiquettes du dimanche + lundi + mardi<br/>
    <strong>Autres jours</strong> → Étiquettes du jour même
    </div>
    
    <h2>🧪 Endpoints de test API :</h2>
    <ul>
        <li><a href="/test/rounds">/test/rounds</a> - 🚚 Test API tournées de livraison</li>
        <li><a href="/test/round/3278">/test/round/[ID]</a> - 📋 Test détails d'une tournée</li>
        <li><a href="/test/order/766809">/test/order/[ID]</a> - 📦 Test API commande</li>
    </ul>
    
    <h2>⚙️ Configuration :</h2>
    <p>Créer un fichier <code>.env</code> avec :</p>
    <pre>
FRESHEO_API_TOKEN=votre_token_ici
FRESHEO_BASE_URL=https://api.fresheo.be
PORT=5001
DEBUG=False
    </pre>
    
    <h2>📋 Version 2.3 :</h2>
    <p>✅ Utilise la nouvelle API <code>GET /rounds/delivery</code><br/>
    ✅ Simulation du jour actuel avec <code>today=</code><br/>
    ✅ Date de livraison forcée avec <code>date=</code><br/>
    ✅ Logique SQL corrigée (vendredi→samedi, samedi→dimanche, dimanche→lundi+mardi)<br/>
    ✅ Noms de fichiers descriptifs</p>
    """

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    debug = os.getenv('DEBUG', 'False').lower() in ['true', '1', 'yes']
    
    app.run(host='0.0.0.0', port=port, debug=debug) 