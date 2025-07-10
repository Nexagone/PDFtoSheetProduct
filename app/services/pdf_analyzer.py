import PyPDF2
import io
import httpx
import json
import asyncio
import logging
from typing import Dict, Any
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)

class PDFAnalyzer:
    def __init__(self):
        self.ollama_url = settings.OLLAMA_URL
        self.model = settings.OLLAMA_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT
        self.max_retries = settings.MAX_RETRIES
        self.retry_delay = settings.RETRY_DELAY

    async def check_ollama_availability(self) -> bool:
        """Vérifie si Ollama est disponible"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                logger.info(f"Vérification de la disponibilité d'Ollama sur {self.ollama_url}")
                response = await client.get(f"{self.ollama_url}/api/tags")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama n'est pas disponible sur {self.ollama_url}: {str(e)}")
            return False

    async def wait_for_ollama(self):
        """Attend que Ollama soit disponible"""
        retries = 0
        while retries < self.max_retries:
            if await self.check_ollama_availability():
                logger.info("Ollama est disponible")
                return True
            retries += 1
            logger.warning(f"Tentative {retries}/{self.max_retries} de connexion à Ollama...")
            await asyncio.sleep(self.retry_delay)
        return False

    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extrait le texte d'un fichier PDF"""
        try:
            logger.info(f"Début de l'extraction du texte du PDF: {pdf_path}")
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for i, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    text += page_text
                    logger.info(f"Page {i+1} extraite, longueur: {len(page_text)} caractères")
                logger.info(f"Extraction terminée, texte total: {len(text)} caractères")
                return text
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction du PDF: {str(e)}", exc_info=True)
            raise Exception(f"Erreur lors de l'extraction du PDF: {str(e)}")

    def extract_json_from_text(self, text: str) -> str:
        """Extrait le JSON de la réponse d'Ollama"""
        start = text.find('{')
        end = text.rfind('}') + 1
        if start == -1 or end == 0:
            raise ValueError("Aucun JSON trouvé dans la réponse")
        return text[start:end]

    def format_json_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Formate la réponse JSON avec des valeurs cohérentes"""
        # Conversion des nombres en chaînes de caractères pour les dimensions
        if "dimensions" in data:
            for key in data["dimensions"]:
                if isinstance(data["dimensions"][key], (int, float)):
                    data["dimensions"][key] = f"{data['dimensions'][key]}mm"
        
        # Conversion du poids en chaîne avec unité
        if "weight" in data and isinstance(data["weight"], (int, float)):
            data["weight"] = f"{data['weight']}kg"
        
        # Conversion de la consommation électrique en chaîne avec unité
        if "power_consumption" in data and isinstance(data["power_consumption"], (int, float)):
            data["power_consumption"] = f"{data['power_consumption']}W"
        
        return data

    async def analyze_with_ollama(self, text: str) -> Dict[str, Any]:
        """Analyse le texte avec Ollama pour extraire les informations produit"""
        prompt = """Analyse le texte suivant et extrait les informations du produit. Retourne UNIQUEMENT un objet JSON valide, sans aucun texte avant ou après. Le JSON doit avoir cette structure exacte, en laissant les champs vides si l'information n'est pas trouvée:
{
    "product_name": "",
    "brand": "",
    "model_number": "",
    "category": "",
    "technical_specs": {
        "volume": "",
        "classe_energetique": "",
        "capacite": "",
        "puissance": "",
        "tension": "",
        "frequence": ""
    },
    "dimensions": {
        "longueur": "",
        "largeur": "",
        "hauteur": "",
        "profondeur": ""
    },
    "weight": "",
    "power_consumption": "",
    "features": [],
    "warranty": "",
    "price_range": "",
    "description": "",
    "color": "",
    "material": "",
    "certifications": []
}

Texte à analyser:
""" + text

        retries = 0
        while retries < self.max_retries:
            try:
                logger.info(f"Tentative {retries + 1}/{self.max_retries} d'analyse avec Ollama")
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    logger.info("Envoi de la requête à Ollama")
                    response = await client.post(
                        f"{self.ollama_url}/api/generate",
                        json={
                            "model": self.model,
                            "prompt": prompt,
                            "stream": False
                        }
                    )
                    response.raise_for_status()
                    result = response.json()
                    logger.info("Réponse reçue d'Ollama")
                    
                    try:
                        json_str = result["response"]
                        logger.info(f"Réponse brute d'Ollama: {json_str[:200]}...")
                        
                        # Extraction du JSON
                        json_str = self.extract_json_from_text(json_str)
                        logger.info(f"JSON extrait: {json_str[:200]}...")
                        
                        parsed_json = json.loads(json_str)
                        logger.info("JSON parsé avec succès")
                        return self.format_json_response(parsed_json)
                    except (json.JSONDecodeError, ValueError) as e:
                        logger.error(f"Erreur de parsing JSON: {str(e)}", exc_info=True)
                        logger.error(f"Contenu reçu: {json_str}")
                        raise Exception("Erreur lors du parsing de la réponse d'Ollama")
            except httpx.ConnectError as e:
                retries += 1
                if retries == self.max_retries:
                    logger.error("Impossible de se connecter à Ollama après plusieurs tentatives")
                    raise Exception(
                        "Service Ollama indisponible. Veuillez vérifier qu'Ollama est en cours d'exécution."
                    )
                logger.warning(f"Échec de la connexion à Ollama, nouvelle tentative dans {self.retry_delay} secondes...")
                await asyncio.sleep(self.retry_delay)
            except httpx.TimeoutException:
                logger.error("Timeout lors de l'appel à Ollama")
                raise Exception("Timeout lors de l'appel à Ollama")
            except Exception as e:
                logger.error(f"Erreur lors de l'analyse: {str(e)}", exc_info=True)
                raise Exception(f"Erreur lors de l'analyse: {str(e)}")

    async def analyze_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """Analyse complète d'un fichier PDF"""
        # Vérification de la disponibilité d'Ollama
        if not await self.wait_for_ollama():
            raise Exception("Ollama n'est pas disponible")
        
        # Extraction du texte
        text = self.extract_text_from_pdf(pdf_path)
        
        # Analyse avec Ollama
        product_data = await self.analyze_with_ollama(text)
        
        return product_data 