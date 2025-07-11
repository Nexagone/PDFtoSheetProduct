#!/bin/bash

echo "🧪 Test de téléchargement des fichiers générés..."
echo ""

# Vérifier que l'application est en cours d'exécution
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "❌ L'application n'est pas accessible"
    exit 1
fi

echo "✅ Application accessible"
echo ""

# Lister les sessions disponibles
echo "📁 Sessions disponibles:"
sessions=$(ls -1 outputs/ 2>/dev/null | head -3)
if [ -z "$sessions" ]; then
    echo "   Aucune session trouvée"
    echo "   Uploadez d'abord un PDF via l'interface web"
    exit 1
fi

for session in $sessions; do
    echo "   - $session"
done

echo ""

# Tester le téléchargement du premier fichier PDF disponible
first_session=$(echo "$sessions" | head -1)
pdf_file="fiche_produit_${first_session}.pdf"
pdf_path="outputs/${first_session}/${pdf_file}"

if [ -f "$pdf_path" ]; then
    echo "📄 Test de téléchargement du fichier PDF..."
    echo "   Session: $first_session"
    echo "   Fichier: $pdf_file"
    echo "   Taille: $(du -h "$pdf_path" | cut -f1)"
    echo ""
    
    # Tester l'endpoint de téléchargement
    response=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/download/${first_session}/${pdf_file}")
    
    if [ "$response" = "200" ]; then
        echo "✅ Téléchargement PDF fonctionne"
    else
        echo "❌ Erreur de téléchargement PDF (HTTP $response)"
    fi
    
    # Tester aussi le fichier HTML
    html_file="fiche_produit_${first_session}.html"
    html_path="outputs/${first_session}/${html_file}"
    
    if [ -f "$html_path" ]; then
        echo ""
        echo "🌐 Test de téléchargement du fichier HTML..."
        echo "   Fichier: $html_file"
        echo "   Taille: $(du -h "$html_path" | cut -f1)"
        echo ""
        
        response=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/download/${first_session}/${html_file}")
        
        if [ "$response" = "200" ]; then
            echo "✅ Téléchargement HTML fonctionne"
        else
            echo "❌ Erreur de téléchargement HTML (HTTP $response)"
        fi
    fi
    
else
    echo "❌ Fichier PDF non trouvé: $pdf_path"
fi

echo ""
echo "🌐 Interface web: http://localhost:8000"
echo ""
echo "📋 Pour tester complètement:"
echo "   1. Ouvrez http://localhost:8000 dans votre navigateur"
echo "   2. Uploadez un PDF"
echo "   3. Cliquez sur les boutons de téléchargement"
echo ""
echo "🔗 URLs de téléchargement direct:"
echo "   PDF: http://localhost:8000/download/${first_session}/${pdf_file}"
echo "   HTML: http://localhost:8000/download/${first_session}/${html_file}" 