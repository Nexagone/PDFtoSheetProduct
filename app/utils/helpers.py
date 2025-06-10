import os
from typing import List, Dict, Any
from pathlib import Path
import json
from loguru import logger

def validate_pdf_file(file_path: str) -> bool:
    """
    Valide un fichier PDF.
    
    Args:
        file_path: Chemin vers le fichier
        
    Returns:
        True si le fichier est valide
    """
    if not os.path.exists(file_path):
        return False
        
    if not file_path.lower().endswith('.pdf'):
        return False
        
    if os.path.getsize(file_path) > int(os.getenv('MAX_UPLOAD_SIZE', 10485760)):
        return False
        
    return True

def sanitize_filename(filename: str) -> str:
    """
    Nettoie et sécurise un nom de fichier.
    
    Args:
        filename: Nom de fichier à nettoyer
        
    Returns:
        Nom de fichier sécurisé
    """
    # Supprime les caractères dangereux
    filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.'))
    return filename.strip()

def format_product_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Formate et nettoie les données produit.
    
    Args:
        data: Données brutes
        
    Returns:
        Données nettoyées
    """
    # Supprime les clés vides
    cleaned = {k: v for k, v in data.items() if v is not None and v != ""}
    
    # Formate les listes
    if "features" in cleaned and isinstance(cleaned["features"], str):
        cleaned["features"] = [f.strip() for f in cleaned["features"].split(",")]
    
    # Normalise les dimensions
    if "dimensions" in cleaned:
        for key in ["longueur", "largeur", "hauteur"]:
            if key in cleaned["dimensions"]:
                dim = cleaned["dimensions"][key]
                if isinstance(dim, (int, float)):
                    cleaned["dimensions"][key] = f"{dim}cm"
                
    return cleaned

def save_to_cache(key: str, data: Any, cache_dir: str = ".cache") -> bool:
    """
    Sauvegarde des données en cache.
    
    Args:
        key: Clé de cache
        data: Données à sauvegarder
        cache_dir: Répertoire de cache
        
    Returns:
        True si la sauvegarde a réussi
    """
    try:
        os.makedirs(cache_dir, exist_ok=True)
        cache_file = Path(cache_dir) / f"{key}.json"
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
        
    except Exception as e:
        logger.error(f"Erreur de mise en cache: {str(e)}")
        return False

def load_from_cache(key: str, cache_dir: str = ".cache") -> Any:
    """
    Charge des données depuis le cache.
    
    Args:
        key: Clé de cache
        cache_dir: Répertoire de cache
        
    Returns:
        Données du cache ou None
    """
    try:
        cache_file = Path(cache_dir) / f"{key}.json"
        if not cache_file.exists():
            return None
            
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    except Exception as e:
        logger.error(f"Erreur de lecture du cache: {str(e)}")
        return None

def create_error_response(error: Exception) -> Dict[str, str]:
    """
    Crée une réponse d'erreur formatée.
    
    Args:
        error: Exception à formater
        
    Returns:
        Dictionnaire d'erreur
    """
    return {
        "error": str(error),
        "type": error.__class__.__name__
    } 