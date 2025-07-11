#!/bin/bash

echo "🔍 Vérification de la configuration GPU pour Ollama..."
echo ""

# Vérifier si nvidia-docker est installé
echo "1. Vérification de nvidia-docker..."
if command -v nvidia-docker &> /dev/null; then
    echo "✅ nvidia-docker est installé"
else
    echo "❌ nvidia-docker n'est pas installé"
    echo "   Installez-le avec: sudo apt-get install nvidia-docker2"
fi

# Vérifier les GPU disponibles
echo ""
echo "2. GPU disponibles:"
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader,nounits
else
    echo "❌ nvidia-smi n'est pas disponible"
fi

# Vérifier si Docker peut accéder aux GPU
echo ""
echo "3. Test d'accès GPU avec Docker..."
if docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi &> /dev/null; then
    echo "✅ Docker peut accéder aux GPU"
else
    echo "❌ Docker ne peut pas accéder aux GPU"
    echo "   Vérifiez que nvidia-docker2 est installé et redémarrez Docker"
fi

# Vérifier l'état d'Ollama
echo ""
echo "4. État d'Ollama:"
if docker ps | grep -q ollama; then
    echo "✅ Ollama est en cours d'exécution"
    
    # Vérifier les logs d'Ollama pour voir s'il utilise la GPU
    echo ""
    echo "5. Logs d'Ollama (dernières lignes):"
    docker logs --tail 10 pdf_analyzer_ollama 2>/dev/null | grep -i "gpu\|cuda\|nvidia" || echo "   Aucune information GPU trouvée dans les logs"
    
    # Tester l'API Ollama
    echo ""
    echo "6. Test de l'API Ollama:"
    if curl -s http://localhost:11434/api/tags &> /dev/null; then
        echo "✅ API Ollama accessible"
        
        # Vérifier les modèles disponibles
        echo ""
        echo "7. Modèles disponibles:"
        curl -s http://localhost:11434/api/tags | jq -r '.models[].name' 2>/dev/null || echo "   Impossible de récupérer les modèles"
    else
        echo "❌ API Ollama non accessible"
    fi
else
    echo "❌ Ollama n'est pas en cours d'exécution"
    echo "   Lancez: docker compose up -d"
fi

echo ""
echo "📋 Recommandations:"
echo "   - Si nvidia-docker2 n'est pas installé: sudo apt-get install nvidia-docker2"
echo "   - Redémarrez Docker après installation: sudo systemctl restart docker"
echo "   - Relancez les services: docker compose down && docker compose up -d"
echo "   - Vérifiez les logs: docker logs pdf_analyzer_ollama" 