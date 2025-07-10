# Générateur de Fiches Produit PDF → HTML/PDF

Un service intelligent qui transforme automatiquement les PDF constructeur en fiches produit professionnelles en utilisant l'IA (Ollama/Llama).

## 🚀 Fonctionnalités

- **Analyse intelligente** : Extraction automatique des informations produit depuis les PDF constructeur
- **Interface moderne** : Interface web drag & drop intuitive
- **Sorties multiples** : Génération de fiches produit en HTML et/ou PDF
- **Design professionnel** : Templates modernes et responsives
- **API REST** : Endpoints pour intégration avec d'autres systèmes
- **Dockerisé** : Déploiement facile avec Docker Compose

## 🏗️ Architecture

```
PDFtoSheetProduct/
├── app/
│   ├── main.py              # Application FastAPI principale
│   ├── config.py            # Configuration
│   ├── services/
│   │   ├── pdf_analyzer.py  # Service d'analyse PDF avec Ollama
│   │   ├── html_generator.py # Générateur HTML
│   │   └── pdf_generator.py  # Générateur PDF
│   └── templates/
│       ├── index.html       # Interface utilisateur
│       └── product_sheet.html # Template fiche produit
├── uploads/                 # Fichiers PDF uploadés
├── outputs/                 # Fichiers générés
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## 🛠️ Installation et Démarrage

### Prérequis

- Docker et Docker Compose
- Au moins 4GB de RAM disponible (pour Ollama)

### Démarrage rapide

1. **Cloner le projet**
```bash
git clone <repository-url>
cd PDFtoSheetProduct
```

2. **Lancer avec Docker Compose**
```bash
docker-compose up -d
```

3. **Accéder à l'application**
- Interface web : http://localhost:8000
- API docs : http://localhost:8000/docs

### Première utilisation

Lors du premier démarrage :
1. Ollama se lance automatiquement
2. Le modèle Llama3 se télécharge (peut prendre plusieurs minutes)
3. L'application attend qu'Ollama soit prêt avant de démarrer

## 📖 Utilisation

### Interface Web

1. **Ouvrir** http://localhost:8000
2. **Glisser-déposer** un fichier PDF constructeur
3. **Choisir** le format de sortie (HTML, PDF, ou les deux)
4. **Cliquer** sur "Générer la fiche produit"
5. **Télécharger** les fichiers générés

### API REST

#### Upload et traitement
```bash
curl -X POST "http://localhost:8000/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf" \
  -F "output_format=both"
```

#### Téléchargement
```bash
curl -X GET "http://localhost:8000/download/{session_id}/{filename}" \
  --output fichier_local.html
```

## 🔧 Configuration

### Variables d'environnement

Créer un fichier `.env` pour personnaliser :

```env
# Configuration Ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3
OLLAMA_TIMEOUT=30

# Configuration des dossiers
UPLOAD_DIR=uploads
OUTPUT_DIR=outputs

# Configuration du serveur
HOST=0.0.0.0
PORT=8000

# Configuration des retries
MAX_RETRIES=3
RETRY_DELAY=2
```

### Modèles Ollama supportés

- `llama3` (recommandé)
- `llama3.2`
- `mistral`
- `codellama`
- Tout autre modèle compatible Ollama

## 📊 Structure des données extraites

Le service extrait automatiquement :

```json
{
  "product_name": "Nom du produit",
  "brand": "Marque",
  "model_number": "Référence modèle",
  "category": "Catégorie",
  "technical_specs": {
    "volume": "Volume",
    "classe_energetique": "Classe énergétique",
    "capacite": "Capacité",
    "puissance": "Puissance",
    "tension": "Tension",
    "frequence": "Fréquence"
  },
  "dimensions": {
    "longueur": "Longueur",
    "largeur": "Largeur", 
    "hauteur": "Hauteur",
    "profondeur": "Profondeur"
  },
  "weight": "Poids",
  "power_consumption": "Consommation électrique",
  "features": ["Fonctionnalité 1", "Fonctionnalité 2"],
  "warranty": "Garantie",
  "price_range": "Gamme de prix",
  "description": "Description détaillée",
  "color": "Couleur",
  "material": "Matériau",
  "certifications": ["Certification 1", "Certification 2"]
}
```

## 🐳 Commandes Docker utiles

### Voir les logs
```bash
# Logs de l'application
docker-compose logs -f app

# Logs d'Ollama
docker-compose logs -f ollama

# Tous les logs
docker-compose logs -f
```

### Redémarrer un service
```bash
docker-compose restart app
```

### Arrêter complètement
```bash
docker-compose down
```

### Nettoyer les volumes
```bash
docker-compose down -v
```

## 🔍 Dépannage

### Ollama ne démarre pas
```bash
# Vérifier les logs
docker-compose logs ollama

# Redémarrer le service
docker-compose restart ollama
```

### Modèle non trouvé
```bash
# Se connecter au conteneur Ollama
docker exec -it pdf_analyzer_ollama bash

# Lister les modèles
ollama list

# Télécharger un modèle
ollama pull llama3
```

### Problèmes de mémoire
- Augmenter la RAM allouée à Docker
- Utiliser un modèle plus léger (mistral au lieu de llama3)

## 🚀 Déploiement en production

### Avec Docker Compose
```bash
# Build en mode production
docker-compose -f docker-compose.prod.yml up -d
```

### Avec Kubernetes
```bash
kubectl apply -f k8s/
```

## 📝 Développement

### Installation locale
```bash
# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Installer les dépendances
pip install -r requirements.txt

# Lancer Ollama localement
ollama serve

# Lancer l'application
uvicorn app.main:app --reload
```

### Tests
```bash
# Tests unitaires
pytest tests/

# Tests d'intégration
pytest tests/integration/
```

## 🤝 Contribution

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/AmazingFeature`)
3. Commit les changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 🆘 Support

- **Issues** : [GitHub Issues](https://github.com/votre-repo/issues)
- **Documentation** : [Wiki](https://github.com/votre-repo/wiki)
- **Email** : support@votre-email.com

---

**Note** : Ce projet nécessite Ollama pour fonctionner. Assurez-vous d'avoir suffisamment de ressources système pour exécuter les modèles d'IA. 