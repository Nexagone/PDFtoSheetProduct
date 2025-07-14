#!/bin/bash

echo "🚀 Démarrage manuel d'Ollama avec Docker standard..."
echo ""

# Arrêter le conteneur Ollama s'il existe
if docker ps -a | grep -q pdf_analyzer_ollama; then
    echo "🛑 Arrêt du conteneur Ollama existant..."
    docker stop pdf_analyzer_ollama
    docker rm pdf_analyzer_ollama
fi

# Supprimer le volume s'il existe (optionnel)
read -p "Voulez-vous supprimer le volume Ollama existant ? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🗑️  Suppression du volume Ollama..."
    docker volume rm pdf_analyzer_ollama_data 2>/dev/null || true
fi

# Démarrer Ollama avec Docker standard
echo "🚀 Démarrage d'Ollama avec --gpus=all..."
docker run -d \
    --name pdf_analyzer_ollama \
    --gpus=all \
    -v ollama_data:/root/.ollama \
    -p 11434:11434 \
    -e OLLAMA_HOST=0.0.0.0 \
    -e OLLAMA_DEBUG=INFO \
    -e OLLAMA_GPU_LAYERS=35 \
    -e OLLAMA_FLASH_ATTENTION=true \
    -e OLLAMA_NUM_PARALLEL=4 \
    -e OLLAMA_KEEP_ALIVE=5m \
    ollama/ollama:latest

# Vérifier le démarrage
echo ""
echo "⏳ Attente du démarrage d'Ollama..."
sleep 10

if docker ps | grep -q pdf_analyzer_ollama; then
    echo "✅ Ollama démarré avec succès !"
    echo "📊 Logs du conteneur:"
    docker logs pdf_analyzer_ollama --tail 10
    
    echo ""
    echo "🌐 Ollama est accessible sur: http://localhost:11434"
    echo "📋 Pour voir les logs en temps réel: docker logs -f pdf_analyzer_ollama"
    echo "🛑 Pour arrêter: docker stop pdf_analyzer_ollama"
else
    echo "❌ Erreur lors du démarrage d'Ollama"
    echo "📋 Logs d'erreur:"
    docker logs pdf_analyzer_ollama
fi 