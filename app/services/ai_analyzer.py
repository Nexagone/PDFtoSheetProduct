import json
from typing import Dict, List, Optional, Any
import httpx
from PIL import Image
import io
import base64
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from ..models.product import ProductSheet

class AIAnalyzer:
    """Service d'analyse IA utilisant Ollama."""

    def __init__(self, ollama_url: str = "http://ollama:11434"):
        """
        Initialise l'analyseur IA.
        
        Args:
            ollama_url: URL du service Ollama
        """
        self.ollama_url = ollama_url
        self.model = "llama3.2-vision:11b"
        self.prompt_template = """Analyse cette documentation produit et extrait les informations suivantes dans un format JSON structuré :
- Nom du produit
- Marque
- Numéro de modèle
- Catégorie
- Spécifications techniques
- Dimensions (longueur, largeur, hauteur)
- Poids
- Consommation électrique
- Fonctionnalités principales
- Garantie
- Fourchette de prix (si disponible)
- Description détaillée

Réponds UNIQUEMENT avec un objet JSON valide contenant ces informations, sans texte supplémentaire.
Si une information n'est pas disponible, utilise null ou une chaîne vide.
Assure-toi que le JSON est correctement formaté et contient toutes les clés requises."""

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def analyze_content(
        self,
        images: List[Image.Image],
        text: str,
        metadata: Dict[str, str]
    ) -> ProductSheet:
        """
        Analyse le contenu extrait du PDF pour générer une fiche produit.
        
        Args:
            images: Liste des images extraites
            text: Texte extrait du PDF
            metadata: Métadonnées du PDF
            
        Returns:
            Fiche produit structurée
        """
        try:
            # Préparation des images pour l'API
            image_data = []
            for img in images[:3]:  # Limite à 3 images pour éviter les timeouts
                buffered = io.BytesIO()
                img.save(buffered, format="JPEG", quality=85)
                img_str = base64.b64encode(buffered.getvalue()).decode()
                image_data.append(img_str)

            # Construction du prompt avec contexte
            full_prompt = f"{self.prompt_template}\n\nMétadonnées du document:\n{json.dumps(metadata, indent=2)}\n\nTexte extrait:\n{text[:1000]}"  # Limite le texte pour éviter les timeouts

            # Préparation de la requête pour Ollama
            request_data = {
                "model": self.model,
                "prompt": full_prompt,
                "images": image_data,
                "stream": False
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json=request_data,
                    timeout=30.0
                )
                response.raise_for_status()
                
                result = response.json()
                response_text = result.get("response", "")

                # Tentative de parsing du JSON
                try:
                    product_data = json.loads(response_text)
                    # Validation et conversion en modèle Pydantic
                    return ProductSheet(**product_data)
                except json.JSONDecodeError as e:
                    logger.error(f"Erreur de parsing JSON: {str(e)}")
                    raise ValueError("L'IA n'a pas retourné un JSON valide")

        except Exception as e:
            logger.error(f"Erreur lors de l'analyse IA: {str(e)}")
            raise ValueError(f"Erreur lors de l'analyse IA: {str(e)}")

    async def health_check(self) -> bool:
        """
        Vérifie la disponibilité du service Ollama.
        
        Returns:
            True si le service est disponible
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.ollama_url}/api/tags")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Erreur de connexion à Ollama: {str(e)}")
            return False 