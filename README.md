# PDF Product Sheet Extractor

API pour extraire automatiquement des fiches produit depuis des documents PDF en utilisant l'IA.

## 🚀 Fonctionnalités

- Extraction de texte et d'images depuis les PDFs
- Analyse multimodale (texte + images) avec Llama 3.2 Vision
- Génération de fiches produit structurées en JSON
- API REST avec documentation OpenAPI
- Support Docker avec orchestration multi-conteneurs
- Optimisé pour Apple Silicon

## 🛠 Prérequis

- Docker et Docker Compose
- 16 Go de RAM minimum recommandés
- macOS, Linux ou Windows avec WSL2
- Connexion Internet pour le premier téléchargement du modèle

## 📦 Installation

1. Clonez le dépôt :
```bash
git clone <repository_url>
cd pdf-product-extractor
```

2. Créez un fichier `.env` à partir du modèle :
```bash
cp .env.example .env
```

3. Démarrez les services :
```bash
docker-compose up -d
```

4. Attendez que le modèle soit téléchargé (première exécution uniquement).

## 🔧 Configuration

Le projet utilise les variables d'environnement suivantes :

- `OLLAMA_URL` : URL du service Ollama (par défaut : http://ollama:11434)
- `MAX_PAGES` : Nombre maximum de pages à traiter par PDF (par défaut : 5)
- `LOG_LEVEL` : Niveau de log (par défaut : INFO)

## 📚 Utilisation de l'API

### Analyse d'un PDF

```bash
curl -X POST "http://localhost:8000/analyze-pdf" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@product_manual.pdf"
```

### Analyse de texte brut

```bash
curl -X POST "http://localhost:8000/analyze-text" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"text": "Description du produit..."}'
```

### Vérification de l'état

```bash
curl "http://localhost:8000/health"
```

## 📊 Format de sortie

L'API retourne une fiche produit structurée au format JSON :

```json
{
  "product_name": "Réfrigérateur XC500",
  "brand": "CoolTech",
  "model_number": "CT-RF500",
  "category": "Électroménager",
  "technical_specs": {
    "volume": "500L",
    "classe_energetique": "A++"
  },
  "dimensions": {
    "longueur": "70cm",
    "largeur": "80cm",
    "hauteur": "180cm"
  },
  "weight": "75kg",
  "power_consumption": "250kWh/an",
  "features": [
    "No Frost",
    "Distributeur d'eau"
  ],
  "warranty": "2 ans",
  "price_range": "800€ - 1000€",
  "description": "Réfrigérateur haut de gamme..."
}
```

## 🔍 Surveillance et Maintenance

### Logs

Les logs sont disponibles via :
```bash
docker-compose logs -f api
```

### Métriques

L'endpoint `/health` fournit des informations sur :
- État du service API
- État du service Ollama
- Utilisation des ressources

## 🛡 Sécurité

- Validation des entrées avec Pydantic
- Nettoyage automatique des fichiers temporaires
- Limitation de la taille des fichiers
- CORS configurable

## ⚡️ Performance

- Optimisation des images avant analyse
- Mise en cache des modèles Ollama
- Traitement asynchrone avec FastAPI
- Retry pattern pour la stabilité

## 🤝 Contribution

1. Fork le projet
2. Créez votre branche (`git checkout -b feature/AmazingFeature`)
3. Committez vos changements (`git commit -m 'Add AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request

## 📝 License

Distribué sous la licence MIT. Voir `LICENSE` pour plus d'informations.

## 🎯 Roadmap

- [ ] Support de formats additionnels (DOCX, Images)
- [ ] Interface utilisateur web
- [ ] Export en différents formats (CSV, XLSX)
- [ ] API de batch processing
- [ ] Support multi-langues
- [ ] Amélioration de la précision du modèle 