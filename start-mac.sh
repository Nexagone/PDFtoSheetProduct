#!/bin/bash

# Script de démarrage pour PDF to Product Sheet Generator (macOS ARM64)

echo "🚀 Démarrage du Générateur de Fiches Produit (macOS ARM64)..."

# Vérifier si Docker est installé
if ! command -v docker &> /dev/null; then
    echo "❌ Docker n'est pas installé. Veuillez installer Docker d'abord."
    exit 1
fi

# Vérifier si Docker Compose est installé
if ! command -v docker compose &> /dev/null; then
    echo "❌ Docker Compose n'est pas installé. Veuillez installer Docker Compose d'abord."
    exit 1
fi

# Créer les dossiers nécessaires
echo "📁 Création des dossiers..."
mkdir -p uploads outputs

# Démarrer les services avec la configuration macOS
echo "🐳 Démarrage des services Docker (macOS ARM64)..."
docker compose -f docker compose.mac.yml up -d

# Attendre que les services soient prêts
echo "⏳ Attente du démarrage des services..."
sleep 15

# Vérifier l'état des services
echo "🔍 Vérification de l'état des services..."

# Vérifier Ollama
if wget --quiet --tries=1 --spider http://localhost:11434/api/tags 2>/dev/null; then
    echo "✅ Ollama est prêt"
else
    echo "⚠️  Ollama démarre encore..."
fi

# Vérifier l'application
if wget --quiet --tries=1 --spider http://localhost:8000/health 2>/dev/null; then
    echo "✅ Application prête"
else
    echo "⚠️  Application démarre encore..."
fi

echo ""
echo "🎉 Services démarrés !"
echo ""
echo "📱 Interface web: http://localhost:8000"
echo "📚 Documentation API: http://localhost:8000/docs"
echo "🔧 Ollama: http://localhost:11434"
echo ""
echo "📋 Commandes utiles:"
echo "  - Voir les logs: docker compose -f docker compose.mac.yml logs -f"
echo "  - Arrêter: docker compose -f docker compose.mac.yml down"
echo "  - Redémarrer: docker compose -f docker compose.mac.yml restart"
echo ""
echo "⚠️  Note: Le premier démarrage peut prendre plusieurs minutes"
echo "    pour télécharger le modèle Llama3."
echo ""
echo "💡 Conseil: Si vous rencontrez des problèmes de performance,"
echo "    vous pouvez utiliser un modèle plus léger comme 'mistral'"
echo "    en modifiant OLLAMA_MODEL dans docker compose.mac.yml" 