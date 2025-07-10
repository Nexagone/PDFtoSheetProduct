@echo off
echo ========================================
echo Arrêt des services PDF Generator
echo ========================================
echo.

echo Arrêt des conteneurs...
docker-compose -f docker-compose.windows.yml down
docker-compose -f docker-compose.mac.yml down

echo.
echo Services arrêtés avec succès !
echo.
pause 