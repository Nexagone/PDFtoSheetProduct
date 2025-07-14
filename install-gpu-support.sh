#!/bin/bash

echo "🚀 Installation du support GPU pour Docker et Ollama..."
echo ""

# Vérifier si on est root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Ce script doit être exécuté en tant que root (sudo)"
    echo "   Utilisez: sudo ./install-gpu-support.sh"
    exit 1
fi

# Vérifier si nvidia-container-toolkit est déjà installé
if dpkg -l | grep -q nvidia-container-toolkit; then
    echo "✅ nvidia-container-toolkit est déjà installé"
else
    echo "📦 Installation de nvidia-container-toolkit..."
    
    # Ajouter le repository NVIDIA
    distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
    curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
    curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
        sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
        tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
    
    # Mettre à jour et installer
    apt-get update
    apt-get install -y nvidia-container-toolkit
    
    echo "✅ nvidia-container-toolkit installé"
fi

# Configurer Docker pour utiliser nvidia runtime
echo "🔧 Configuration du runtime nvidia pour Docker..."
nvidia-ctk runtime configure --runtime=docker
systemctl restart docker

# Tester l'installation
echo ""
echo "🧪 Test de l'installation..."
if docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi &> /dev/null; then
    echo "✅ Installation réussie ! Docker peut accéder aux GPU"
else
    echo "❌ Problème avec l'installation"
    echo "   Vérifiez que les pilotes NVIDIA sont installés"
fi

echo ""
echo "📋 Prochaines étapes:"
echo "   1. Relancez vos services: docker compose down && docker compose up -d"
echo "   2. Vérifiez la configuration: ./check-gpu.sh"
echo "   3. Surveillez les logs: docker logs pdf_analyzer_ollama" 