#!/bin/bash

echo "🧪 Test de la sauvegarde des réponses du modèle..."
echo ""

# Vérifier que l'application est en cours d'exécution
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "❌ L'application n'est pas en cours d'exécution"
    echo "   Démarrez d'abord: docker compose up -d"
    exit 1
fi

echo "✅ Application en cours d'exécution"
echo ""

# Créer un fichier PDF de test simple
echo "📄 Création d'un fichier PDF de test..."
cat > test_document.txt << EOF
FICHE TECHNIQUE - RÉFRIGÉRATEUR SAMSUNG

Nom du produit: Réfrigérateur Side by Side Samsung
Modèle: RS68N8220S9
Marque: Samsung
Catégorie: Électroménager

Description: Réfrigérateur Side by Side avec distributeur d'eau et de glace intégré.

Spécifications techniques:
- Tension: 220-240V
- Fréquence: 50Hz
- Classe énergétique: A+++
- Couleur: Inox
- Écran: Écran tactile LED

Dimensions: Non spécifiées
Poids: Non spécifié

Fonctionnalités:
- Distributeur d'eau et de glace
- Écran tactile LED
- Classe énergétique A+++
- Système de refroidissement Twin Cooling Plus

Certifications: CE, RoHS
Garantie: 2 ans
EOF

# Convertir en PDF (si pandoc est disponible)
if command -v pandoc &> /dev/null; then
    pandoc test_document.txt -o test_document.pdf
    test_file="test_document.pdf"
    echo "✅ Fichier PDF créé avec pandoc"
else
    # Créer un fichier texte comme alternative
    cp test_document.txt test_document.pdf
    test_file="test_document.pdf"
    echo "⚠️  Pandoc non disponible, utilisation d'un fichier texte"
fi

echo ""

# Envoyer le fichier à l'API
echo "🚀 Envoi du fichier à l'API..."
response=$(curl -s -X POST "http://localhost:8000/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@$test_file" \
  -F "output_format=html")

echo "📋 Réponse de l'API:"
echo "$response" | jq . 2>/dev/null || echo "$response"

echo ""

# Extraire le session_id de la réponse
session_id=$(echo "$response" | grep -o '"session_id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$session_id" ]; then
    echo "❌ Impossible d'extraire le session_id"
    exit 1
fi

echo "🆔 Session ID: $session_id"
echo ""

# Attendre un peu pour que le traitement se termine
echo "⏳ Attente du traitement..."
sleep 10

# Vérifier que les fichiers ont été créés
echo "🔍 Vérification des fichiers créés..."

output_dir="outputs/$session_id"
if [ -d "$output_dir" ]; then
    echo "✅ Dossier de sortie créé: $output_dir"
    
    # Vérifier les fichiers générés
    if [ -f "$output_dir/product_sheet.html" ]; then
        echo "✅ Fichier HTML généré"
    else
        echo "❌ Fichier HTML manquant"
    fi
    
    # Vérifier les réponses du modèle
    model_responses_dir="$output_dir/model_responses"
    if [ -d "$model_responses_dir" ]; then
        echo "✅ Dossier des réponses du modèle créé"
        
        # Compter les fichiers de réponse
        response_count=$(find "$model_responses_dir" -name "*.json" | wc -l)
        echo "📊 Nombre de réponses sauvegardées: $response_count"
        
        # Afficher le contenu d'une réponse
        if [ $response_count -gt 0 ]; then
            echo ""
            echo "📋 Exemple de réponse sauvegardée:"
            first_response=$(find "$model_responses_dir" -name "*.json" | head -1)
            echo "Fichier: $first_response"
            
            # Afficher les métadonnées
            echo ""
            echo "📊 Métadonnées:"
            jq '.metadata' "$first_response" 2>/dev/null || echo "   Impossible de parser le JSON"
            
            # Afficher les statistiques
            echo ""
            echo "📈 Statistiques:"
            jq '.analysis_info' "$first_response" 2>/dev/null || echo "   Impossible de parser le JSON"
            
            # Afficher les données extraites principales
            echo ""
            echo "✅ Données extraites principales:"
            jq '.parsed_data | {product_name, brand, model_number, category}' "$first_response" 2>/dev/null || echo "   Impossible de parser le JSON"
        fi
    else
        echo "❌ Dossier des réponses du modèle manquant"
    fi
else
    echo "❌ Dossier de sortie manquant"
fi

echo ""

# Nettoyer les fichiers de test
echo "🧹 Nettoyage des fichiers de test..."
rm -f test_document.txt test_document.pdf

echo ""
echo "🎯 Test terminé !"
echo ""
echo "📋 Commandes utiles pour analyser les réponses:"
echo "   python view-model-responses.py"
echo "   python cleanup-model-responses.py list" 