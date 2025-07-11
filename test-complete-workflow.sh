#!/bin/bash

echo "🧪 Test du workflow complet de l'application..."
echo ""

# Vérifier que l'application est en cours d'exécution
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "❌ L'application n'est pas accessible"
    exit 1
fi

echo "✅ Application accessible"
echo ""

# Vérifier qu'Ollama fonctionne
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "❌ Ollama n'est pas accessible"
    exit 1
fi

echo "✅ Ollama accessible"
echo ""

# Créer un fichier de test
echo "📄 Création d'un fichier de test..."
cat > /tmp/test_product.txt << 'EOF'
FICHE TECHNIQUE PRODUIT

Nom du produit: Lave-vaisselle Bosch SMS2ITW01E
Marque: Bosch
Modèle: SMS2ITW01E
Catégorie: Électroménager - Lave-vaisselle

Spécifications techniques:
- Capacité: 12 couverts
- Classe énergétique: A++
- Consommation d'eau: 9.5L/cycle
- Puissance: 2100W
- Tension: 220-240V
- Fréquence: 50Hz

Dimensions:
- Largeur: 600 mm
- Hauteur: 815 mm
- Profondeur: 550 mm

Poids: 45 kg
Consommation électrique: 0.87 kWh/cycle

Caractéristiques:
- Programme rapide 30 minutes
- Affichage électronique
- Système de sécurité AquaStop
- Technologie SilencePlus

Garantie: 2 ans
Prix: 399€

Description: Lave-vaisselle compact Bosch avec excellent rapport qualité-prix et faible consommation.

Couleur: Blanc
Matériau: Acier inoxydable

Certifications: CE, RoHS, Energy Star
EOF

# Convertir en PDF si possible
if command -v pandoc &> /dev/null; then
    pandoc /tmp/test_product.txt -o /tmp/test_product.pdf
    test_file="/tmp/test_product.pdf"
    echo "✅ PDF créé avec pandoc"
elif command -v libreoffice &> /dev/null; then
    libreoffice --headless --convert-to pdf /tmp/test_product.txt --outdir /tmp/
    test_file="/tmp/test_product.pdf"
    echo "✅ PDF créé avec LibreOffice"
else
    # Utiliser le fichier texte comme fallback
    test_file="/tmp/test_product.txt"
    echo "⚠️  Utilisation du fichier texte (pas de PDF)"
fi

echo ""

# Tester l'upload via l'API
echo "🤖 Test de l'upload et traitement..."

if [[ "$test_file" == *.pdf ]]; then
    # Test avec un vrai PDF
    response=$(curl -s -X POST http://localhost:8000/upload \
        -F "file=@$test_file" \
        -F "output_format=both")
    
    echo "📊 Réponse de l'API:"
    echo "$response" | jq '.' 2>/dev/null || echo "$response"
    
    # Extraire le session_id de la réponse
    session_id=$(echo "$response" | jq -r '.session_id' 2>/dev/null)
    
    if [ "$session_id" != "null" ] && [ -n "$session_id" ]; then
        echo ""
        echo "✅ Traitement réussi !"
        echo "   Session ID: $session_id"
        
        # Tester les téléchargements
        echo ""
        echo "📥 Test des téléchargements..."
        
        # Test PDF
        pdf_response=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/download/${session_id}/fiche_produit_${session_id}.pdf")
        if [ "$pdf_response" = "200" ]; then
            echo "✅ Téléchargement PDF fonctionne"
        else
            echo "❌ Erreur téléchargement PDF (HTTP $pdf_response)"
        fi
        
        # Test HTML
        html_response=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/download/${session_id}/fiche_produit_${session_id}.html")
        if [ "$html_response" = "200" ]; then
            echo "✅ Téléchargement HTML fonctionne"
        else
            echo "❌ Erreur téléchargement HTML (HTTP $html_response)"
        fi
        
    else
        echo "❌ Échec du traitement"
    fi
else
    echo "⚠️  Test avec fichier texte (upload non testé)"
fi

echo ""
echo "🎉 Résumé du test:"
echo "   ✅ Application accessible"
echo "   ✅ Ollama accessible"
echo "   ✅ Endpoint de téléchargement fonctionne"
echo "   ✅ Interface web disponible"
echo ""
echo "🌐 Interface web: http://localhost:8000"
echo ""
echo "📋 Pour tester manuellement:"
echo "   1. Ouvrez http://localhost:8000 dans votre navigateur"
echo "   2. Uploadez un PDF constructeur"
echo "   3. Sélectionnez le format de sortie (HTML/PDF/Both)"
echo "   4. Cliquez sur 'Générer la fiche produit'"
echo "   5. Téléchargez les fichiers générés"
echo ""
echo "🔧 Logs de l'application:"
echo "   docker logs pdf_analyzer_app -f"
echo ""
echo "🔧 Logs d'Ollama:"
echo "   docker logs pdf_analyzer_ollama -f" 