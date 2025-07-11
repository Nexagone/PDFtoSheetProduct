#!/bin/bash

echo "🧪 Test de traitement PDF avec l'application..."
echo ""

# Vérifier que l'application est en cours d'exécution
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "❌ L'application n'est pas accessible"
    exit 1
fi

echo "✅ Application accessible"
echo ""

# Créer un fichier PDF de test simple
echo "📄 Création d'un fichier PDF de test..."

# Créer un fichier texte avec des informations produit
cat > /tmp/test_product.txt << 'EOF'
FICHE TECHNIQUE PRODUIT

Nom du produit: Réfrigérateur Samsung RT38K501J8A
Marque: Samsung
Modèle: RT38K501J8A
Catégorie: Électroménager - Réfrigérateur

Spécifications techniques:
- Volume total: 380 litres
- Classe énergétique: A+++
- Capacité congélateur: 101 litres
- Capacité réfrigérateur: 279 litres
- Puissance: 150W
- Tension: 220-240V
- Fréquence: 50Hz

Dimensions:
- Largeur: 595 mm
- Hauteur: 1775 mm
- Profondeur: 650 mm

Poids: 67 kg
Consommation électrique: 150 kWh/an

Caractéristiques:
- Système de refroidissement No Frost
- Éclairage LED
- Affichage électronique
- Compartiment fraîcheur

Garantie: 2 ans
Prix: 599€

Description: Réfrigérateur combiné Samsung avec système No Frost, grande capacité de stockage et excellente efficacité énergétique.

Couleur: Inox
Matériau: Acier inoxydable

Certifications: CE, RoHS
EOF

# Convertir en PDF (si disponible)
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
    echo "⚠️  Pandoc/LibreOffice non disponible, utilisation du fichier texte"
fi

echo ""

# Tester l'API d'analyse
echo "🤖 Test de l'API d'analyse..."

# Lire le contenu du fichier
if [[ "$test_file" == *.pdf ]]; then
    # Pour un PDF, on ne peut pas lire directement le contenu
    echo "📋 Fichier PDF créé: $test_file"
    echo "   (Pour tester l'API complète, uploadez ce fichier via l'interface web)"
else
    # Pour un fichier texte, on peut tester l'extraction
    content=$(cat "$test_file")
    echo "📋 Contenu du fichier:"
    echo "$content" | head -10
    echo "..."
fi

echo ""
echo "🌐 Interface web disponible sur: http://localhost:8000"
echo ""
echo "📋 Pour tester complètement:"
echo "   1. Ouvrez http://localhost:8000 dans votre navigateur"
echo "   2. Uploadez le fichier: $test_file"
echo "   3. Vérifiez que l'analyse fonctionne correctement"
echo ""
echo "📊 Logs de l'application:"
echo "   docker logs pdf_analyzer_app -f"
echo ""
echo "📊 Logs d'Ollama:"
echo "   docker logs pdf_analyzer_ollama -f" 