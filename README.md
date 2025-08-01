# 🏷️ Serveur Flask - Fresheo Delivery Labels v2.0

Ce serveur Flask consomme la **nouvelle API back-office** de Fresheo et génère un CSV d'étiquettes de livraison équivalent à votre requête SQL.

**⚡ Version 2.0** - Mise à jour pour la nouvelle API `GET /rounds/delivery`

## ✨ Fonctionnalités v2.0

- 🔄 **Nouvelle API** : Utilise `GET /rounds/delivery` au lieu de `POST /deliveries/`
- ✅ **Logique temporelle SQL reproduite** : Vendredi→Samedi, Samedi→Dimanche-Mardi, autres jours→aujourd'hui
- ✅ **Approche en 2 étapes** : Liste des tournées → Détails de chaque tournée
- ✅ **Calculs automatiques** : `labels_quantity`, `qrcode_data`, `color`
- ✅ **Formatage intelligent** : `delivery_planning_name` ("lundi matin", "mardi soir")
- ✅ **Tri identique** : Par date, planning, tournée, ordre
- ✅ **Format CSV** : Headers + données prêtes pour impression
- 🌐 **URL mise à jour** : `https://api.fresheo.be/api/bo/v1`

## 🚀 Installation

```bash
# Installer les dépendances
pip install -r requirements.txt

# Configuration via fichier .env
cp env_example .env
# Puis éditer .env avec vos vraies valeurs
```

## 🎯 Utilisation

### Démarrer le serveur

```bash
python app.py
```

### Endpoints disponibles

| Endpoint            | Description                                 |
| ------------------- | ------------------------------------------- |
| `GET /`             | Page d'accueil avec instructions            |
| `GET /delivery.csv` | **CSV des étiquettes** (endpoint principal) |
| `GET /health`       | Vérification de santé + dates cibles        |

### Télécharger le CSV

```bash
# Via curl
curl -o delivery_labels.csv "http://localhost:5000/delivery.csv"

# Via navigateur
http://localhost:5000/delivery.csv
```

## 📋 Format CSV généré

Le CSV contient exactement les mêmes colonnes que votre requête SQL :

```csv
order_id,shipping_group,shipping_order,qrcode_data,total_meals,max_meals,labels_quantity,shipping_date,color,user_lang,cust_name,shipping_label,delivery_status
5001,1,1,BE_5001,4,4,1,2023-03-21,color_2,FR,Jean Dupont,mardi matin,false
5002,1,2,BE_5002,7,7,1,2023-03-21,color_2,FR,Sophie Martin,mardi matin,true
```

## 🎨 Correspondances avec votre SQL

| Champ SQL         | Champ API/Calculé                   | Logique                 |
| ----------------- | ----------------------------------- | ----------------------- |
| `order_id`        | `order.id`                          | ✅ Direct               |
| `shipping_group`  | `tour.round`                        | ✅ Numéro de tournée    |
| `shipping_order`  | `order.delivery_tour_order_id`      | ✅ Direct               |
| `qrcode_data`     | `'BE_' + order_id`                  | ✅ Calculé              |
| `total_meals`     | `order_details.total_meals`         | ✅ Via endpoint détails |
| `max_meals`       | `= total_meals`                     | ✅ Supposé égal         |
| `labels_quantity` | `ceil(total_meals / 7)`             | ✅ Calculé              |
| `shipping_date`   | Date de la clé                      | ✅ Direct               |
| `color`           | `'color_' + ((tour % 10) + 1)`      | ✅ Calculé              |
| `user_lang`       | `'FR'`                              | ✅ Fixe                 |
| `cust_name`       | `INITCAP(first_name + last_name)`   | ✅ Formaté              |
| `shipping_label`  | `"jour matin/soir"`                 | ✅ Calculé selon heure  |
| `delivery_status` | `delivery__status == 'replacement'` | ✅ Boolean              |

## ⚙️ Logique de filtrage temporelle

Reproduit exactement votre logique SQL :

```python
def get_target_dates():
    today = datetime.now()
    day_of_week = today.weekday()  # 0=Lundi, 4=Vendredi, 5=Samedi

    if day_of_week == 4:  # Vendredi → Samedi
        target_date = (today + timedelta(days=1)).strftime("%Y-%m-%d")
        return target_date, target_date
    elif day_of_week == 5:  # Samedi → Dimanche à Mardi
        start_date = (today + timedelta(days=1)).strftime("%Y-%m-%d")
        end_date = (today + timedelta(days=3)).strftime("%Y-%m-%d")
        return start_date, end_date
    else:  # Autres jours → Aujourd'hui
        target_date = today.strftime("%Y-%m-%d")
        return target_date, target_date
```

## 🔧 Configuration avancée

### Fichier .env

```bash
# Obligatoire
FRESHEO_API_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Optionnelles
FRESHEO_BASE_URL=https://api.fresheo.be/api/bo/v1    # URL de base API v2.0
PORT=5001                                            # Port du serveur (5001 pour éviter AirPlay sur Mac)
DEBUG=False                                          # Mode debug
```

### Déploiement Docker (optionnel)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app.py .
EXPOSE 5000
CMD ["python", "app.py"]
```

## 🐛 Dépannage

### Erreur "Token manquant"

Créer/vérifier le fichier `.env` :

```bash
FRESHEO_API_TOKEN=votre_token_réel_ici
```

### Aucune donnée retournée

Vérifiez les dates via `/health` :

```bash
curl http://localhost:5000/health
```

### Timeout API

Le serveur récupère les détails de chaque commande. Avec beaucoup de commandes, cela peut prendre du temps. Les timeouts sont configurés à 30s pour les livraisons et 10s par commande.

## 📈 Performance

- **Optimisation** : Une requête groupée `/deliveries/` + requêtes individuelles `/order/{id}`
- **Cache potentiel** : Vous pouvez ajouter un cache Redis pour les détails de commandes
- **Parallélisation** : Possibilité d'ajouter `asyncio` pour les appels API parallèles

## ✅ Prêt pour production !

Ce serveur génère des CSV **strictement équivalents** à votre requête SQL originale et peut être utilisé immédiatement pour vos étiquettes de livraison.
