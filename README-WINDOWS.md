# PDF to Product Sheet Generator - Guide Windows

## Prérequis

### 1. Docker Desktop
- Télécharger et installer [Docker Desktop pour Windows](https://www.docker.com/products/docker-desktop/)
- S'assurer que Docker Desktop est en cours d'exécution

### 2. Support GPU (Optionnel mais recommandé)
Pour de meilleures performances, installez le support GPU :

#### NVIDIA GPU
1. Installer les [pilotes NVIDIA](https://www.nvidia.com/Download/index.aspx)
2. Installer [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html#docker)
3. Redémarrer Docker Desktop

#### AMD GPU
1. Installer les [pilotes AMD](https://www.amd.com/en/support)
2. Installer [AMD ROCm](https://rocmdocs.amd.com/en/latest/deploy/linux/prerequisites.html)

## Installation et démarrage

### Méthode simple (recommandée)
1. Double-cliquer sur `start-windows.bat`
2. Le script détectera automatiquement votre configuration GPU/CPU
3. L'interface sera disponible sur http://localhost:8000

### Méthode manuelle

#### Avec GPU NVIDIA
```cmd
docker-compose -f docker-compose.windows.yml up -d
```

#### Sans GPU (CPU uniquement)
```cmd
docker-compose -f docker-compose.mac.yml up -d
```

## Vérification de l'installation

### Vérifier les services
```cmd
docker-compose -f docker-compose.windows.yml ps
```

### Vérifier les logs
```cmd
docker-compose -f docker-compose.windows.yml logs ollama
```

### Tester l'API
```cmd
curl http://localhost:8000/health
```

## Optimisations GPU

Le fichier `docker-compose.windows.yml` inclut automatiquement :
- `OLLAMA_GPU_LAYERS=35` : Utilise GPU pour toutes les couches
- `OLLAMA_FLASH_ATTENTION=true` : Optimisation de l'attention
- `OLLAMA_NUM_PARALLEL=4` : Parallélisation
- `OLLAMA_KEEP_ALIVE=5m` : Garde le modèle en mémoire

## Dépannage

### Problème de GPU non détecté
```cmd
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
```

### Problème de permissions
- Exécuter Docker Desktop en tant qu'administrateur
- Vérifier les paramètres de partage de fichiers dans Docker Desktop

### Problème de mémoire
- Augmenter la mémoire allouée à Docker Desktop (8GB minimum recommandé)
- Réduire `OLLAMA_NUM_PARALLEL` si nécessaire

## Performance attendue

### Avec GPU NVIDIA
- Modèle Llama 3.1 8B : ~5-15 secondes par analyse
- Timeout configuré à 90 secondes

### Avec CPU uniquement
- Modèle Llama 3.1 8B : ~30-60 secondes par analyse
- Timeout configuré à 180 secondes

## Utilisation

1. Ouvrir http://localhost:8000 dans votre navigateur
2. Glisser-déposer un fichier PDF
3. Attendre l'analyse (plus rapide avec GPU)
4. Télécharger la fiche produit générée

## Arrêt des services

```cmd
docker-compose -f docker-compose.windows.yml down
```

Ou utiliser le script `stop-windows.bat` si disponible. 