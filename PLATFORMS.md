# Support des Plateformes

Ce projet supporte plusieurs plateformes avec des configurations optimisées.

## 🍎 macOS (ARM64 - Apple Silicon)

### Configuration recommandée
```bash
# Utiliser le script macOS optimisé
./start-mac.sh

# Ou manuellement
docker-compose -f docker-compose.mac.yml up -d
```

### Caractéristiques
- ✅ Optimisé pour Apple Silicon (M1/M2/M3)
- ✅ Performance native ARM64
- ✅ Support complet d'Ollama
- ⚠️ Nécessite Docker Desktop pour Mac

### Modèles recommandés
- `llama3` (recommandé)
- `mistral` (plus rapide, moins précis)
- `codellama` (pour le code)

## 🐧 Linux (x86_64)

### Configuration recommandée
```bash
# Utiliser le script standard
./start.sh

# Ou manuellement
docker-compose up -d
```

### Caractéristiques
- ✅ Performance optimale
- ✅ Support complet
- ✅ Compatible avec tous les modèles

## 🪟 Windows

### Configuration recommandée
```bash
# Utiliser le script standard
./start.sh

# Ou manuellement
docker-compose up -d
```

### Caractéristiques
- ✅ Support via Docker Desktop
- ⚠️ Performance légèrement réduite
- ⚠️ Nécessite WSL2 pour de meilleures performances

## 🔧 Configuration des Modèles

### Modèles légers (recommandés pour débuter)
```yaml
# Dans docker-compose.yml ou docker-compose.mac.yml
environment:
  - OLLAMA_MODEL=mistral
```

### Modèles complets (plus précis, plus lents)
```yaml
environment:
  - OLLAMA_MODEL=llama3
```

## 📊 Comparaison des Performances

| Modèle | Taille | RAM | Vitesse | Précision |
|--------|--------|-----|---------|-----------|
| mistral | ~4GB | 8GB | ⚡⚡⚡ | ⭐⭐⭐ |
| llama3 | ~8GB | 16GB | ⚡⚡ | ⭐⭐⭐⭐⭐ |
| codellama | ~7GB | 14GB | ⚡⚡ | ⭐⭐⭐⭐ |

## 🚨 Dépannage par Plateforme

### macOS ARM64
```bash
# Problème de plateforme
docker-compose -f docker-compose.mac.yml down
docker-compose -f docker-compose.mac.yml up -d

# Problème de mémoire
# Augmenter la RAM allouée à Docker Desktop
```

### Linux
```bash
# Problème de permissions
sudo chown -R $USER:$USER uploads outputs

# Problème de ports
sudo netstat -tulpn | grep :8000
```

### Windows
```bash
# Problème WSL2
wsl --update
wsl --shutdown

# Problème de performance
# Activer WSL2 dans Docker Desktop
```

## 🔄 Migration entre Plateformes

### De macOS vers Linux
```bash
# Sauvegarder les données
docker-compose -f docker-compose.mac.yml down
cp -r uploads uploads_backup
cp -r outputs outputs_backup

# Restaurer sur Linux
docker-compose up -d
cp -r uploads_backup/* uploads/
cp -r outputs_backup/* outputs/
```

### De Linux vers macOS
```bash
# Même procédure inversée
docker-compose down
cp -r uploads uploads_backup
cp -r outputs outputs_backup

# Restaurer sur macOS
docker-compose -f docker-compose.mac.yml up -d
cp -r uploads_backup/* uploads/
cp -r outputs_backup/* outputs/
``` 