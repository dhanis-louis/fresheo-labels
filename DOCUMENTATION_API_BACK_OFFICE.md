# Documentation API Back-Office Fresheo

## Vue d'ensemble

Cette documentation décrit l'API back-office de Fresheo permettant de gérer les tournées de livraison et d'accéder aux informations nécessaires pour l'impression d'étiquettes de livraison.

**⚠️ Documentation mise à jour** : Cette documentation a été corrigée pour refléter l'API actuelle. L'ancien endpoint `POST /deliveries/` a été remplacé par `GET /rounds/delivery`.

## 🔑 Authentification

L'API utilise l'authentification Django avec permissions administrateur. Tous les endpoints requièrent :

- **Permission** : `IsAdminUser`
- **Headers requis** :
  ```http
  Authorization: Bearer <token>
  Content-Type: application/json
  ```

## 📍 URL de base

```
https://api.fresheo.be/api/bo/v1/
```

**Note :** L'URL de base peut varier selon l'environnement :

- **Production** : `https://api.fresheo.be/api/bo/v1/`
- **Développement** : `https://dev.fresheo.be/api/bo/v1/`

---

## 🚛 Endpoints Livraison

### 1. Récupérer toutes les tournées de livraison pour une date

```http
GET /rounds/delivery?date={yyyy-mm-dd}
```

**Description :** Récupère la liste des tournées de livraison pour une date spécifique.

**Headers requis :**

```http
Authorization: Bearer <token>
Content-Type: application/json
```

**Paramètres de requête :**

- `date` : Date au format `yyyy-mm-dd` (obligatoire) - ex: `2023-03-21`

**Structure TypeScript de la réponse :**

```typescript
// Structure de la réponse - tableau des tournées
interface DeliveryRoundResponse extends Array<DeliveryRound> {}

interface DeliveryRound {
  id: number; // ID unique de la tournée
  timeOfDay: string; // Heure de la tournée (ex: "09:00")
  shippingDate: string; // Date de livraison au format "YYYY-MM-DD"
  round: number; // Numéro de la tournée
  roundLength: number; // Nombre total de commandes dans la tournée
  ordersShipped: number; // Nombre de commandes déjà livrées
}
```

**Exemple de réponse :**

```json
[
  {
    "id": 123,
    "timeOfDay": "09:00",
    "shippingDate": "2023-03-21",
    "round": 1,
    "roundLength": 15,
    "ordersShipped": 12
  },
  {
    "id": 124,
    "timeOfDay": "13:00",
    "shippingDate": "2023-03-21",
    "round": 2,
    "roundLength": 25,
    "ordersShipped": 20
  },
  {
    "id": 125,
    "timeOfDay": "17:00",
    "shippingDate": "2023-03-21",
    "round": 3,
    "roundLength": 18,
    "ordersShipped": 0
  }
]
```

**Codes d'erreur spécifiques :**

**400 - Paramètre manquant :**

```json
{
  "error": "date parameter is required"
}
```

**400 - Format de date incorrect :**

```json
{
  "error": "Invalid date format. Expected yyyy-mm-dd"
}
```

**Notes importantes pour cet endpoint :**

1. **Date unique** : Contrairement à l'ancienne version, cet endpoint ne prend qu'une seule date, pas une plage
2. **Méthode GET** : L'endpoint utilise maintenant GET au lieu de POST
3. **Paramètre de requête** : La date est passée en query parameter `?date=yyyy-mm-dd`
4. **Réponse simplifiée** : Retourne un tableau simple des tournées avec leurs statistiques de base
5. **Pour les détails** : Utilisez l'endpoint `/rounds/delivery/{id}` pour obtenir les détails d'une tournée spécifique
6. **Performance** : Cet endpoint est optimisé pour donner un aperçu rapide des tournées du jour

---

## 🚚 Endpoints Tournées (Rounds)

### 1. Récupérer toutes les tournées pour une date

```http
GET /rounds/{action}?date={yyyy-mm-dd}
```

**Paramètres :**

- `action` : `delivery` ou `prep`
- `date` : Date au format `yyyy-mm-dd` (ex: `2023-03-21`)

**Réponse pour action=delivery :**

```json
[
  {
    "id": 123,
    "timeOfDay": "09:00",
    "shippingDate": "2023-03-21",
    "round": 1,
    "roundLength": 15,
    "ordersShipped": 12
  }
]
```

### 2. Récupérer une tournée spécifique

```http
GET /rounds/{action}/{round_id}
```

**Paramètres :**

- `action` : `delivery` ou `prep`
- `round_id` : ID de la tournée

**Réponse pour action=delivery :**

```json
{
  "id": 123,
  "timeOfDay": "09:00",
  "round": 1,
  "roundLength": 15,
  "orders": [
    {
      "id": 5001,
      "index": 1,
      "customerName": "Jean Dupont",
      "shipping_time": "09:30",
      "firstDelivery": false,
      "isActive": true,
      "isDelivered": false,
      "deliveryStatus": null
    }
  ],
  "gasPrice": 0,
  "mileage": 0,
  "commentary": null,
  "hasTakenPicBefore": false,
  "hasTakenPicAfter": false
}
```

---

## 📦 Endpoints Commandes

### 1. Récupérer les détails d'une commande

```http
GET /order/{order_id}
GET /order/{order_id}/{order_type}
```

**Paramètres :**

- `order_id` : ID de la commande
- `order_type` : `delivery` ou `order-prep` (optionnel)

**Réponse pour order_type=delivery :**

```json
[
  {
    "id": 5001,
    "customer": {
      "first_name": "Jean",
      "last_name": "Dupont",
      "email": "jean.dupont@email.com",
      "phone": "+32123456789",
      "first_shipping": false,
      "third_shipping": false,
      "vip": false
    },
    "address": {
      "first_line": "123 Rue de la Paix",
      "second_line": "Apt 4B",
      "zip_code": "1000",
      "city": "Bruxelles",
      "country": "BE",
      "phone": "+32123456789",
      "time_slot": {
        "shipping_day": 1,
        "shipping_time": {
          "start": "09:00",
          "end": "13:00"
        }
      },
      "notes": ["Sonner à l'interphone", "Bâtiment accessible par l'arrière"]
    },
    "subscription_id": 456,
    "discovery": false,
    "desserts": 2,
    "shipping_date": "21/03/2023",
    "is_paid": true,
    "is_active": true,
    "is_closed": true,
    "is_shipped": false,
    "is_ready": true,
    "total_meals": 4,
    "preparator": {
      "first_name": "Marie",
      "last_name": "Martin",
      "email": "marie.martin@fresheo.com"
    },
    "deliveryman": {
      "first_name": "Paul",
      "last_name": "Bernard",
      "email": "paul.bernard@fresheo.com"
    },
    "meals": [
      {
        "internal_id": 1,
        "plan": 1,
        "qr_uuid": "abc123-def456-789",
        "picture": "https://cdn.fresheo.com/meals/meal1.jpg",
        "thumbnail": "https://cdn.fresheo.com/meals/meal1_thumb.jpg",
        "quantity": 2
      }
    ]
  }
]
```

---

## 🖨️ Guide d'utilisation pour impression d'étiquettes

### Scenario typique : Impression des étiquettes du jour

**1. Récupérer les tournées du jour via GET /rounds/delivery :**

```bash
curl -X GET "https://api.fresheo.be/api/bo/v1/rounds/delivery?date=2023-03-21" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json"
```

**2. Parcourir la liste des tournées :**

```python
response = api_call_result  # Liste des tournées
for round_data in response:
    print(f"Tournée {round_data['round']} à {round_data['timeOfDay']}")
    print(f"  - ID: {round_data['id']}")
    print(f"  - Date: {round_data['shippingDate']}")
    print(f"  - Commandes: {round_data['ordersShipped']}/{round_data['roundLength']}")

    # Pour obtenir les détails des commandes, faire un appel à /rounds/delivery/{id}
```

### Format des données pour étiquettes

Pour créer des étiquettes, vous devez d'abord récupérer les tournées avec GET /rounds/delivery, puis récupérer les détails de chaque tournée avec GET /rounds/delivery/{id}.

**Données disponibles dans les détails d'une tournée :**

- **Nom client** : `order.customerName`
- **Heure de livraison** : `order.shipping_time` (ou `order.deliveryTime`)
- **Statut livraison** : `order.deliveryStatus`
- **Numéro de commande** : `order.id`
- **Position dans tournée** : `order.index`
- **Première livraison** : `order.firstDelivery` (booléen)
- **Commande active** : `order.isActive`
- **Commande livrée** : `order.isDelivered`

**Note :** Pour obtenir des informations détaillées sur le client (email, préparateur, livreur), utilisez l'endpoint `/get-order/{id}/delivery`.

### Script Python d'exemple mis à jour

```python
import requests
import json
from datetime import datetime
from typing import Dict, List, Any

class FresheoDeliveryAPI:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

    def get_delivery_rounds_for_date(self, date: str) -> List[Dict[str, Any]]:
        """Récupère toutes les tournées pour une date donnée"""
        url = f"{self.base_url}/rounds/delivery"
        params = {'date': date}
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_round_details(self, round_id: int) -> Dict[str, Any]:
        """Récupère les détails d'une tournée spécifique"""
        url = f"{self.base_url}/rounds/delivery/{round_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_order_details(self, order_id: int) -> List[Dict[str, Any]]:
        """Récupère les détails complets d'une commande (pour informations supplémentaires)"""
        url = f"{self.base_url}/get-order/{order_id}/delivery"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def extract_all_orders_for_printing(self, date: str) -> List[Dict[str, Any]]:
        """Extrait toutes les commandes du jour dans un format simple pour impression"""
        orders_for_printing = []

        # 1. Récupérer toutes les tournées du jour
        rounds = self.get_delivery_rounds_for_date(date)

        # 2. Pour chaque tournée, récupérer les détails
        for round_data in rounds:
            round_details = self.get_round_details(round_data['id'])

            # 3. Extraire les commandes de cette tournée
            for order in round_details.get('orders', []):
                label_data = {
                    'order_id': order['id'],
                    'customer_name': order['customerName'],
                    'shipping_date': date,
                    'shipping_time': order.get('shipping_time') or order.get('deliveryTime'),
                    'delivery_status': order['deliveryStatus'],
                    'tour_round': round_data['round'],
                    'tour_position': order['index'],
                    'is_shipped': order['isDelivered'],
                    'is_active': order['isActive'],
                    'is_first_delivery': order['firstDelivery'],
                    'time_slot': round_data['timeOfDay'],
                    'tour_id': round_data['id'],
                    'round_length': round_data['roundLength'],
                    'orders_shipped': round_data['ordersShipped']
                }
                orders_for_printing.append(label_data)

        return orders_for_printing

# Utilisation
api = FresheoDeliveryAPI("https://api.fresheo.be/api/bo/v1", "your-token")

# Récupérer toutes les commandes du jour
date = datetime.now().strftime("%Y-%m-%d")
orders_for_labels = api.extract_all_orders_for_printing(date)

# Générer les étiquettes
for order in orders_for_labels:
    print(f"=== ÉTIQUETTE COMMANDE {order['order_id']} ===")
    print(f"Client: {order['customer_name']}")
    print(f"Date: {order['shipping_date']}")
    print(f"Heure: {order['shipping_time']}")
    print(f"Tournée: {order['tour_round']} - Position: {order['tour_position']}")
    print(f"Créneau: {order['time_slot']}")
    print(f"Statut: {'LIVRÉ' if order['is_shipped'] else 'EN ATTENTE'}")
    print(f"Première livraison: {'OUI' if order['is_first_delivery'] else 'NON'}")
    print("=" * 50)

# Si vous avez besoin de plus d'informations (email, préparateur, livreur)
# Utilisez api.get_order_details(order_id) pour chaque commande
```

---

## 📱 Codes de réponse HTTP

- **200** : Succès
- **400** : Erreur dans la requête
- **401** : Non autorisé
- **404** : Ressource non trouvée
- **500** : Erreur serveur

---

## ⚠️ Notes importantes

1. **Limites de temps** : Les requêtes pour récupérer plusieurs commandes ont une limite de 30 secondes
2. **Permissions** : Tous les endpoints nécessitent des droits administrateur
3. **Cache** : Les données de tournées peuvent être mises en cache côté client
4. **Tâches asynchrones** : Les exports d'étiquettes utilisent Celery et sont traités en arrière-plan
5. **Nouvelle approche** : L'ancienne API /deliveries/ a été remplacée par une approche en deux étapes avec /rounds/delivery

---

## 🔧 Dépannage

### Erreur d'authentification

```json
{
  "detail": "Authentication credentials were not provided."
}
```

**Solution :** Vérifier que le token d'authentification est valide et inclus dans les headers.

### Erreur de format de date sur /rounds/delivery

```json
{
  "error": "Invalid date format. Expected yyyy-mm-dd"
}
```

**Solution :** Vérifier que le paramètre `date` respecte le format `yyyy-mm-dd`.

---

Cette documentation vous permet de développer votre système d'impression d'étiquettes en interfaçant directement avec l'API back-office de Fresheo.
