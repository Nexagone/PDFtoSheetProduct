#!/bin/bash

echo "🇫🇷 Test de la réponse en français..."
echo ""

# Vérifier que l'application est en cours d'exécution
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "❌ L'application n'est pas en cours d'exécution"
    echo "   Démarrez d'abord: docker compose up -d"
    exit 1
fi

echo "✅ Application en cours d'exécution"
echo ""

# Créer un fichier PDF de test en anglais
echo "📄 Création d'un fichier PDF de test en anglais..."
cat > test_english_document.txt << EOF
TECHNICAL SPECIFICATION - SAMSUNG REFRIGERATOR

Product Name: Samsung Side by Side Refrigerator
Model: RS68N8220S9
Brand: Samsung
Category: Home Appliances

Description: Side by Side refrigerator with integrated water and ice dispenser.

Technical Specifications:
- Voltage: 220-240V
- Frequency: 50Hz
- Energy Class: A+++
- Color: Stainless Steel
- Display: LED Touch Screen

Dimensions: Not specified
Weight: Not specified

Features:
- Water and ice dispenser
- LED touch screen
- Energy class A+++
- Twin Cooling Plus system

Certifications: CE, RoHS
Warranty: 2 years
EOF

# Convertir en PDF (si pandoc est disponible)
if command -v pandoc &> /dev/null; then
    pandoc test_english_document.txt -o test_english_document.pdf
    test_file="test_english_document.pdf"
    echo "✅ Fichier PDF créé avec pandoc"
else
    # Créer un fichier texte comme alternative
    cp test_english_document.txt test_english_document.pdf
    test_file="test_english_document.pdf"
    echo "⚠️  Pandoc non disponible, utilisation d'un fichier texte"
fi

echo ""

# Envoyer le fichier à l'API
echo "🚀 Envoi du fichier anglais à l'API..."
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
sleep 15

# Vérifier que les fichiers ont été créés
echo "🔍 Vérification des fichiers créés..."

output_dir="outputs/$session_id"
if [ -d "$output_dir" ]; then
    echo "✅ Dossier de sortie créé: $output_dir"
    
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
            echo "📋 Analyse de la réponse pour vérifier le français:"
            first_response=$(find "$model_responses_dir" -name "*.json" | head -1)
            echo "Fichier: $first_response"
            
            # Extraire et afficher les données parsées
            echo ""
            echo "🇫🇷 DONNÉES EXTRACTES (doivent être en français):"
            parsed_data=$(jq -r '.parsed_data' "$first_response" 2>/dev/null)
            
            if [ "$parsed_data" != "null" ]; then
                # Vérifier les champs principaux
                product_name=$(echo "$parsed_data" | jq -r '.product_name // "N/A"')
                brand=$(echo "$parsed_data" | jq -r '.brand // "N/A"')
                description=$(echo "$parsed_data" | jq -r '.description // "N/A"')
                
                echo "   Nom du produit: $product_name"
                echo "   Marque: $brand"
                echo "   Description: $description"
                
                # Vérifier s'il y a du texte en anglais
                echo ""
                echo "🔍 VÉRIFICATION DE LA LANGUE:"
                
                # Mots-clés anglais à détecter
                english_keywords=("refrigerator" "side" "water" "ice" "dispenser" "energy" "class" "stainless" "steel" "touch" "screen" "warranty" "years")
                french_keywords=("réfrigérateur" "côté" "eau" "glace" "distributeur" "énergie" "classe" "inox" "acier" "tactile" "écran" "garantie" "ans")
                
                found_english=0
                found_french=0
                
                for keyword in "${english_keywords[@]}"; do
                    if echo "$parsed_data" | grep -qi "$keyword"; then
                        echo "   ⚠️  Mot anglais détecté: $keyword"
                        found_english=$((found_english + 1))
                    fi
                done
                
                for keyword in "${french_keywords[@]}"; do
                    if echo "$parsed_data" | grep -qi "$keyword"; then
                        echo "   ✅ Mot français détecté: $keyword"
                        found_french=$((found_french + 1))
                    fi
                done
                
                echo ""
                echo "📊 RÉSULTAT:"
                if [ $found_english -eq 0 ] && [ $found_french -gt 0 ]; then
                    echo "   ✅ EXCELLENT - Réponse entièrement en français"
                elif [ $found_english -gt 0 ] && [ $found_french -gt 0 ]; then
                    echo "   ⚠️  MIXTE - Réponse partiellement en français ($found_english mots anglais, $found_french mots français)"
                elif [ $found_english -gt 0 ] && [ $found_french -eq 0 ]; then
                    echo "   ❌ PROBLÈME - Réponse entièrement en anglais"
                else
                    echo "   ❓ INDÉTERMINÉ - Aucun mot-clé détecté"
                fi
                
            else
                echo "   ❌ Impossible de lire les données parsées"
            fi
            
            # Afficher la réponse brute pour analyse
            echo ""
            echo "📝 RÉPONSE BRUTE (premiers 500 caractères):"
            raw_response=$(jq -r '.raw_response' "$first_response" 2>/dev/null)
            if [ "$raw_response" != "null" ]; then
                echo "${raw_response:0:500}..."
            else
                echo "   Impossible de lire la réponse brute"
            fi
            
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
rm -f test_english_document.txt test_english_document.pdf

echo ""
echo "🎯 Test terminé !"
echo ""
echo "💡 Si des mots anglais sont détectés, le prompt doit être renforcé." 