#!/bin/bash

echo "🔍 Vérification de la configuration GPU..."
echo ""

# Vérifier les pilotes NVIDIA
echo "📊 Pilotes NVIDIA:"
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader,nounits
else
    echo "❌ nvidia-smi non trouvé - pilotes NVIDIA non installés"
fi

echo ""

# Vérifier nvidia-container-toolkit
echo "📦 nvidia-container-toolkit:"
if dpkg -l | grep -q nvidia-container-toolkit; then
    echo "✅ Installé"
else
    echo "❌ Non installé"
fi

echo ""

# Vérifier nvidia-docker2
echo "📦 nvidia-docker2:"
if dpkg -l | grep -q nvidia-docker2; then
    echo "⚠️  Installé (peut être désinstallé avec ./uninstall-nvidia-docker2.sh)"
else
    echo "✅ Non installé"
fi

echo ""

# Tester Docker avec GPU
echo "🐳 Test Docker GPU:"
if docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi &> /dev/null; then
    echo "✅ Docker peut accéder aux GPU"
else
    echo "❌ Docker ne peut pas accéder aux GPU"
fi

echo ""

# Vérifier les conteneurs Ollama
echo "🤖 Conteneurs Ollama:"
if docker ps | grep -q ollama; then
    echo "✅ Ollama en cours d'exécution"
    docker ps --filter "name=ollama" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
else
    echo "❌ Ollama non démarré"
fi

echo ""

# Vérifier la configuration Docker
echo "🔧 Configuration Docker:"
if [ -f "/etc/docker/daemon.json" ]; then
    echo "📋 Fichier de configuration Docker trouvé:"
    cat /etc/docker/daemon.json | jq . 2>/dev/null || cat /etc/docker/daemon.json
else
    echo "📋 Aucun fichier de configuration Docker personnalisé"
fi

echo ""
echo "📋 Commandes utiles:"
echo "   - Installer GPU: sudo ./install-gpu-support.sh"
echo "   - Désinstaller nvidia-docker2: sudo ./uninstall-nvidia-docker2.sh"
echo "   - Démarrer Ollama manuellement: ./start-ollama-manual.sh"
echo "   - Voir les logs: docker logs pdf_analyzer_ollama" 