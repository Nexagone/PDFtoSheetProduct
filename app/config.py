from pydantic_settings import BaseSettings
from pathlib import Path
import os

class Settings(BaseSettings):
    # Configuration Ollama
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"  # Retour au modèle original
    OLLAMA_TIMEOUT: int = 180  # Timeout augmenté à 3 minutes
    
    # Configuration des dossiers
    UPLOAD_DIR: str = "uploads"
    OUTPUT_DIR: str = "outputs"
    
    # Configuration du serveur
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Configuration des retries
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 2
    
    class Config:
        env_file = ".env"

settings = Settings() 