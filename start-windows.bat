@echo off
echo ========================================
echo PDF to Product Sheet Generator - Windows
echo ========================================
echo.

REM Vérifier si Docker Desktop est en cours d'exécution
echo Vérification de Docker Desktop...
docker version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERREUR: Docker Desktop n'est pas en cours d'exécution.
    echo Veuillez démarrer Docker Desktop et réessayer.
    pause
    exit /b 1
)

REM Vérifier si NVIDIA Container Toolkit est disponible (optionnel)
echo Vérification du support GPU...
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi >nul 2>&1
if %errorlevel% equ 0 (
    echo GPU NVIDIA détecté - Optimisations activées
    set COMPOSE_FILE=docker-compose.windows.yml
) else (
    echo GPU non détecté - Utilisation CPU
    set COMPOSE_FILE=docker-compose.mac.yml
)

echo.
echo Démarrage des services...
echo Fichier de configuration: %COMPOSE_FILE%
echo.

REM Arrêter les conteneurs existants
docker-compose -f %COMPOSE_FILE% down

REM Démarrer les services
docker-compose -f %COMPOSE_FILE% up -d

echo.
echo Services démarrés avec succès !
echo.
echo Interface web: http://localhost:8000
echo API Ollama: http://localhost:11434
echo.
echo Appuyez sur une touche pour voir les logs...
pause

REM Afficher les logs
docker-compose -f %COMPOSE_FILE% logs -f 