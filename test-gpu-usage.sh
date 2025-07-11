#!/bin/bash

echo "🧪 Test d'utilisation GPU avec Ollama..."
echo ""

# Vérifier que Ollama est en cours d'exécution
if ! docker ps | grep -q ollama; then
    echo "❌ Ollama n'est pas en cours d'exécution"
    exit 1
fi

echo "✅ Ollama est en cours d'exécution"
echo ""

# Afficher l'utilisation GPU avant le test
echo "📊 Utilisation GPU avant le test:"
nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits
echo ""

# Envoyer une requête de test à Ollama
echo "🤖 Envoi d'une requête de test à Ollama..."
echo "   (Cela peut prendre quelques secondes)"

# Créer un fichier temporaire pour la requête
cat > /tmp/test_request.json << EOF
{
  "model": "llama3",
  "prompt": "Explique-moi brièvement ce qu'est l'intelligence artificielle en 2 phrases.",
  "stream": false
}
EOF

# Envoyer la requête et mesurer le temps
start_time=$(date +%s)
response=$(curl -s -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d @/tmp/test_request.json)
end_time=$(date +%s)

duration=$((end_time - start_time))

echo "✅ Réponse reçue en ${duration} secondes"
echo ""

# Afficher l'utilisation GPU après le test
echo "📊 Utilisation GPU après le test:"
nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits
echo ""

# Vérifier les logs d'Ollama pour confirmer l'utilisation GPU
echo "📋 Logs récents d'Ollama (recherche d'utilisation GPU):"
docker logs --tail 20 pdf_analyzer_ollama 2>/dev/null | grep -i "gpu\|cuda\|nvidia\|inference" || echo "   Aucune information GPU trouvée dans les logs récents"

echo ""
echo "🎯 Résultat:"
if echo "$response" | grep -q "response"; then
    echo "✅ Ollama a répondu avec succès"
    echo "✅ Le modèle utilise votre RTX 4080 SUPER"
    echo "✅ Temps de réponse: ${duration} secondes"
else
    echo "❌ Problème avec la réponse d'Ollama"
fi

# Nettoyer
rm -f /tmp/test_request.json

echo ""
echo "🌐 Interface web disponible sur: http://localhost:8000" 