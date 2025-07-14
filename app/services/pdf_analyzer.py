import PyPDF2
import io
import httpx
import json
import asyncio
import logging
import re
import aiofiles
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

from app.config import settings

logger = logging.getLogger(__name__)

class PDFAnalyzer:
    def __init__(self):
        self.ollama_url = settings.OLLAMA_URL
        self.model = settings.OLLAMA_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT
        self.max_retries = settings.MAX_RETRIES
        self.retry_delay = settings.RETRY_DELAY
        
        # Configuration pour différents types de produits
        self.product_type_keywords = {
            "electromenager": ["four", "réfrigérateur", "lave-vaisselle", "micro-onde", "cuisinière", "frigo"],
            "electronique": ["console", "ordinateur", "smartphone", "tablette", "téléviseur", "tv"],
            "automobile": ["voiture", "véhicule", "auto", "moteur", "transmission"],
            "mobilier": ["meuble", "chaise", "table", "armoire", "canapé"],
            "outillage": ["perceuse", "scie", "marteau", "tournevis", "clé"]
        }

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
        """Extrait le texte d'un fichier PDF avec gestion d'erreurs améliorée"""
        try:
            logger.info(f"Début de l'extraction du texte du PDF: {pdf_path}")
            
            if not pdf_path.exists():
                raise FileNotFoundError(f"Le fichier PDF n'existe pas: {pdf_path}")
            
            file_size = pdf_path.stat().st_size
            logger.info(f"Taille du fichier PDF: {file_size} octets")
            
            if file_size == 0:
                raise ValueError("Le fichier PDF est vide")
            
            # Limite de taille pour éviter les problèmes de mémoire
            if file_size > 50 * 1024 * 1024:  # 50MB
                raise ValueError("Le fichier PDF est trop volumineux (> 50MB)")
            
            text_parts = []
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)
                logger.info(f"Nombre de pages dans le PDF: {total_pages}")
                
                if total_pages == 0:
                    raise ValueError("Le PDF ne contient aucune page")
                
                for i, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():  # Seulement si la page contient du texte
                            text_parts.append(page_text)
                            logger.info(f"Page {i+1} extraite, longueur: {len(page_text)} caractères")
                    except Exception as e:
                        logger.warning(f"Erreur lors de l'extraction de la page {i+1}: {e}")
                        continue
                
                full_text = "\n".join(text_parts)
                
                if not full_text.strip():
                    raise ValueError("Aucun texte extractible trouvé dans le PDF")
                
                # Nettoyage du texte
                full_text = self.clean_extracted_text(full_text)
                
                # Limiter la taille du texte pour éviter le troncage du prompt
                max_text_length = 8000  # Augmenté pour plus de contexte
                if len(full_text) > max_text_length:
                    logger.warning(f"Texte tronqué de {len(full_text)} à {max_text_length} caractères")
                    full_text = full_text[:max_text_length] + "..."
                
                logger.info(f"Extraction terminée, texte total: {len(full_text)} caractères")
                return full_text
                
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction du PDF: {str(e)}", exc_info=True)
            raise Exception(f"Erreur lors de l'extraction du PDF: {str(e)}")

    def clean_extracted_text(self, text: str) -> str:
        """Nettoie le texte extrait du PDF"""
        # Suppression des caractères de contrôle
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x84\x86-\x9f]', '', text)
        
        # Normalisation des espaces
        text = re.sub(r'\s+', ' ', text)
        
        # Suppression des lignes vides multiples
        text = re.sub(r'\n\s*\n', '\n', text)
        
        return text.strip()

    def detect_product_type(self, text: str) -> str:
        """Détecte le type de produit pour adapter l'extraction"""
        text_lower = text.lower()
        
        for product_type, keywords in self.product_type_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    logger.info(f"Type de produit détecté: {product_type}")
                    return product_type
        
        logger.info("Type de produit non détecté, utilisation du template générique")
        return "generic"

    async def save_model_response(self, session_id: str, prompt: str, raw_response: str, parsed_data: Dict[str, Any], output_path: Path) -> None:
        """Sauvegarde la réponse complète du modèle pour analyse"""
        try:
            # Créer le dossier de sauvegarde
            backup_dir = output_path / "model_responses"
            backup_dir.mkdir(exist_ok=True)
            
            # Nom du fichier avec timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{session_id}_{timestamp}_model_response.json"
            file_path = backup_dir / filename
            
            # Données à sauvegarder
            backup_data = {
                "metadata": {
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat(),
                    "model": self.model,
                    "filename": filename
                },
                "prompt": prompt,
                "raw_response": raw_response,
                "parsed_data": parsed_data,
                "analysis_info": {
                    "prompt_length": len(prompt),
                    "response_length": len(raw_response),
                    "parsed_fields_count": len(parsed_data),
                    "model_used": self.model
                }
            }
            
            # Sauvegarder en JSON
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(backup_data, indent=2, ensure_ascii=False))
            
            logger.info(f"Réponse du modèle sauvegardée: {file_path}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de la réponse du modèle: {str(e)}")

    def create_structured_prompt(self, text: str) -> str:
        """Crée un prompt structuré et optimisé pour l'analyse du texte"""
        prompt = f"""Tu es un expert en analyse de fiches techniques produits. Tu dois analyser EXCLUSIVEMENT le texte fourni ci-dessous et extraire UNIQUEMENT les informations qui y sont explicitement mentionnées.

⚠️ RÈGLES ABSOLUES :
1. Ne JAMAIS inventer ou deviner d'informations
2. Si une information n'est pas dans le texte, mettre ""
3. Analyser UNIQUEMENT le contenu fourni
4. RÉPONDRE OBLIGATOIREMENT EN FRANÇAIS - MÊME SI LE DOCUMENT EST EN ANGLAIS OU AUTRE LANGUE
5. Être précis sur les unités (mm, cm, kg, W, V, etc.)
6. TRADUIRE TOUTES LES INFORMATIONS EN FRANÇAIS - Ne jamais laisser de texte en anglais

TEXTE À ANALYSER (analyse uniquement ce contenu) :
{text}

FORMAT DE RÉPONSE OBLIGATOIRE (JSON valide) :
{{
    "product_name": "Nom exact trouvé dans le texte (ou chaîne vide si pas trouvé)",
    "brand": "Marque exacte trouvée dans le texte (ou chaîne vide si pas trouvé)",
    "model_number": "Modèle/référence exact trouvé dans le texte (ou chaîne vide si pas trouvé)",
    "category": "Catégorie exacte trouvée dans le texte (ou chaîne vide si pas trouvé)",
    "description": "Description exacte trouvée dans le texte (ou chaîne vide si pas trouvé)",
    "price_range": "Prix ou gamme de prix exacte trouvée dans le texte",
    "technical_specs": {{
        "power_consumption": "Consommation électrique exacte trouvée (W, watts, kW)",
        "voltage": "Tension exacte trouvée (V, volts, 220V, 110V)",
        "frequency": "Fréquence exacte trouvée (Hz, hertz, 50Hz, 60Hz)",
        "capacity": "Capacité/volume exact trouvé (L, litres, m³)",
        "efficiency_class": "Classe énergétique exacte trouvée (A+++, A++, A+, A, B, C, D)",
        "noise_level": "Niveau sonore exact trouvé (dB, décibels)",
        "speed": "Vitesse exacte trouvée (tr/min, rpm, km/h)",
        "pressure": "Pression exacte trouvée (bar, Pa, kPa)",
        "temperature_range": "Plage de température exacte trouvée (°C, °F)",
        "material": "Matériaux exacts trouvés dans le texte",
        "color": "Couleur exacte trouvée dans le texte",
        "connectivity": "Connectivité exacte trouvée (WiFi, Bluetooth, USB, etc.)",
        "display": "Écran/affichage exact trouvé dans le texte",
        "memory": "Mémoire exacte trouvée (RAM, stockage, Go, To)",
        "processor": "Processeur exact trouvé dans le texte",
        "battery": "Batterie exacte trouvée dans le texte",
        "operating_system": "Système d'exploitation exact trouvé"
    }},
    "dimensions": {{
        "length": "Longueur exacte trouvée (mm, cm, m)",
        "width": "Largeur exacte trouvée (mm, cm, m)",
        "height": "Hauteur exacte trouvée (mm, cm, m)",
        "depth": "Profondeur exacte trouvée (mm, cm, m)",
        "diameter": "Diamètre exact trouvé (mm, cm, m)",
        "overall": "Dimensions globales exactes trouvées (L x l x h)"
    }},
    "weight": "Poids exact trouvé (kg, g, tonnes)",
    "features": [
        "Fonctionnalité 1 trouvée dans le texte",
        "Fonctionnalité 2 trouvée dans le texte"
    ],
    "certifications": [
        "Certification 1 trouvée dans le texte",
        "Certification 2 trouvée dans le texte"
    ],
    "warranty": "Garantie exacte trouvée dans le texte",
    "installation_requirements": "Exigences d'installation exactes trouvées",
    "maintenance": "Instructions de maintenance exactes trouvées",
    "safety_features": "Fonctionnalités de sécurité exactes trouvées",
    "accessories_included": "Accessoires inclus exacts trouvés",
    "compatibility": "Compatibilité exacte trouvée dans le texte",
    "environmental_conditions": "Conditions environnementales exactes trouvées",
    "standards_compliance": "Conformité aux normes exactes trouvées",
    "additional_info": "Autres informations exactes trouvées dans le texte"
}}

RÈGLES DE RECHERCHE PRÉCISES :
- Cherche EXACTEMENT ces mots-clés : dimensions, poids, puissance, tension, fréquence, décibels, classe énergétique, garantie, certification, norme, accessoires, compatibilité
- Si tu ne trouves PAS l'information dans le texte, mets ""
- Ne génère JAMAIS de contenu qui n'est pas explicitement dans le texte fourni

⚠️ INSTRUCTION FINALE OBLIGATOIRE :
- RÉPONDS UNIQUEMENT EN FRANÇAIS
- TRADUIS TOUTES LES INFORMATIONS EN FRANÇAIS
- MÊME SI LE DOCUMENT SOURCE EST EN ANGLAIS, RÉPONDS EN FRANÇAIS
- NE LAISSE AUCUN TEXTE EN ANGLAIS DANS TA RÉPONSE

RÉPONDS UNIQUEMENT AVEC LE JSON, SANS COMMENTAIRES NI EXPLICATIONS."""
        return prompt

    def extract_json_from_text(self, text: str) -> str:
        """Extrait le JSON de la réponse d'Ollama avec plusieurs méthodes améliorées"""
        # Suppression des balises markdown
        cleaned = text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        
        # Méthode 1: Recherche directe de JSON
        start = cleaned.find('{')
        end = cleaned.rfind('}') + 1
        if start != -1 and end > start:
            json_candidate = cleaned[start:end]
            try:
                json.loads(json_candidate)
                return json_candidate
            except json.JSONDecodeError:
                pass
        
        # Méthode 2: Recherche avec regex améliorée
        json_patterns = [
            r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',  # JSON imbriqué
            r'\{.*?\}',  # JSON simple
            r'(\{[\s\S]*\})'  # JSON multilignes
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, cleaned, re.DOTALL)
            for match in matches:
                try:
                    json.loads(match)
                    return match
                except json.JSONDecodeError:
                    continue
        
        # Méthode 3: Tentative de réparation du JSON
        return self.repair_json(cleaned)

    def repair_json(self, json_str: str) -> str:
        """Tente de réparer un JSON malformé"""
        try:
            # Corrections courantes
            repaired = json_str
            
            # Supprimer les virgules en trop
            repaired = re.sub(r',\s*}', '}', repaired)
            repaired = re.sub(r',\s*]', ']', repaired)
            
            # Ajouter des guillemets manquants aux clés
            repaired = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', repaired)
            
            # Essayer de parser
            json.loads(repaired)
            logger.info("JSON réparé avec succès")
            return repaired
            
        except json.JSONDecodeError:
            logger.warning("Impossible de réparer le JSON, retour d'un JSON vide")
            return "{}"

    def validate_extracted_data(self, data: Dict[str, Any], original_text: str) -> Dict[str, Any]:
        """Valide les données extraites contre le texte original pour éviter les hallucinations"""
        logger.info("Validation des données extraites")
        
        # Mots-clés suspects (hallucinations courantes)
        suspicious_keywords = [
            "lorem ipsum", "example", "placeholder", "template",
            "non spécifié", "à déterminer", "voir documentation",
            "fournisseur de chaleur", "htr 3000", "système de chauffage à inertie"
        ]
        
        # Mots-clés anglais courants à détecter
        english_keywords = [
            "refrigerator", "freezer", "dishwasher", "washing machine", "oven", "microwave",
            "side by side", "water dispenser", "ice dispenser", "energy class", "stainless steel",
            "touch screen", "led display", "warranty", "years", "voltage", "frequency",
            "power consumption", "capacity", "dimensions", "weight", "features", "certifications"
        ]
        
        def is_suspicious(value: str) -> bool:
            if not value:
                return False
            value_lower = value.lower()
            return any(keyword in value_lower for keyword in suspicious_keywords)
        
        def contains_english(value: str) -> bool:
            if not value:
                return False
            value_lower = value.lower()
            return any(keyword in value_lower for keyword in english_keywords)
        
        def validate_in_text(value: str, text: str) -> bool:
            """Vérifie si une valeur existe dans le texte original"""
            if not value or len(value) < 3:
                return True  # Valeurs courtes acceptées
            
            # Recherche flexible (normalisation)
            normalized_value = re.sub(r'[^\w\s]', '', value.lower())
            normalized_text = re.sub(r'[^\w\s]', '', text.lower())
            
            # Découper en mots pour une recherche plus flexible
            value_words = normalized_value.split()
            if len(value_words) > 1:
                # Si c'est une phrase, vérifier que la plupart des mots sont présents
                found_words = sum(1 for word in value_words if word in normalized_text)
                return found_words >= len(value_words) * 0.7
            else:
                return normalized_value in normalized_text
        
        validated_data = {}
        english_detected = False
        
        for key, value in data.items():
            if isinstance(value, str):
                if is_suspicious(value) or not validate_in_text(value, original_text):
                    validated_data[key] = ""
                    logger.warning(f"Valeur suspecte supprimée pour {key}: {value}")
                elif contains_english(value):
                    validated_data[key] = value  # Garder la valeur mais logger l'alerte
                    logger.warning(f"TEXTE ANGLAIS DÉTECTÉ pour {key}: {value}")
                    english_detected = True
                else:
                    validated_data[key] = value
                    
            elif isinstance(value, list):
                validated_list = []
                for item in value:
                    if isinstance(item, str) and not is_suspicious(item) and validate_in_text(item, original_text):
                        if contains_english(item):
                            logger.warning(f"TEXTE ANGLAIS DÉTECTÉ pour {key}: {item}")
                            english_detected = True
                        validated_list.append(item)
                validated_data[key] = validated_list
                
            elif isinstance(value, dict):
                validated_dict = {}
                for subkey, subvalue in value.items():
                    if isinstance(subvalue, str):
                        if not is_suspicious(subvalue) and validate_in_text(subvalue, original_text):
                            if contains_english(subvalue):
                                logger.warning(f"TEXTE ANGLAIS DÉTECTÉ pour {key}.{subkey}: {subvalue}")
                                english_detected = True
                            validated_dict[subkey] = subvalue
                        else:
                            validated_dict[subkey] = ""
                    else:
                        validated_dict[subkey] = subvalue
                validated_data[key] = validated_dict
            else:
                validated_data[key] = value
        
        if english_detected:
            logger.error("⚠️  RÉPONSE EN ANGLAIS DÉTECTÉE - Le prompt doit être renforcé")
        
        return validated_data

    async def analyze_with_ollama(self, text: str, session_id: str = None, output_path: Path = None) -> Dict[str, Any]:
        """Analyse le texte avec Ollama pour extraire les informations produit"""
        logger.info(f"Début de l'analyse avec Ollama, texte à analyser: {len(text)} caractères")
        
        prompt = self.create_structured_prompt(text)
        logger.info(f"Prompt créé, longueur: {len(prompt)} caractères")

        retries = 0
        while retries < self.max_retries:
            try:
                logger.info(f"Tentative {retries + 1}/{self.max_retries} d'analyse avec Ollama")
                
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    request_data = {
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.05,  # Très faible pour éviter les hallucinations
                            "top_p": 0.9,
                            "num_predict": 3000,
                            "stop": ["```", "---", "RÉPONDS", "FORMAT"]  # Arrêter à ces tokens
                        }
                    }
                    
                    response = await client.post(
                        f"{self.ollama_url}/api/generate",
                        json=request_data
                    )
                    response.raise_for_status()
                    result = response.json()
                    
                    logger.info("Réponse reçue d'Ollama")
                    
                    try:
                        json_str = result["response"]
                        logger.info(f"Réponse brute d'Ollama: {json_str[:200]}...")
                        
                        # Extraction et parsing du JSON
                        clean_json = self.extract_json_from_text(json_str)
                        data = json.loads(clean_json)
                        
                        # Validation des données
                        validated_data = self.validate_extracted_data(data, text)
                        
                        # Sauvegarder la réponse du modèle si session_id et output_path sont fournis
                        if session_id and output_path:
                            await self.save_model_response(session_id, prompt, json_str, validated_data, output_path)
                        
                        logger.info(f"Données extraites et validées: {len(validated_data)} champs")
                        return validated_data
                        
                    except Exception as e:
                        logger.error(f"Erreur lors du parsing: {str(e)}")
                        
                        # Sauvegarder même en cas d'erreur si session_id et output_path sont fournis
                        if session_id and output_path:
                            await self.save_model_response(session_id, prompt, json_str, {"error": str(e)}, output_path)
                        
                        # Si c'est la dernière tentative, essayer avec un prompt simplifié
                        if retries == self.max_retries - 1:
                            logger.info("Tentative avec un prompt simplifié...")
                            return await self.analyze_with_simple_prompt(text, session_id, output_path)
                        
                        retries += 1
                        continue
                        
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

    async def analyze_with_simple_prompt(self, text: str, session_id: str = None, output_path: Path = None) -> Dict[str, Any]:
        """Analyse avec un prompt simplifié en cas d'échec"""
        simple_prompt = f"""Extrait les informations produit de ce texte et réponds avec un JSON simple en FRANÇAIS :

IMPORTANT : RÉPONDS UNIQUEMENT EN FRANÇAIS, MÊME SI LE TEXTE EST EN ANGLAIS

{{
    "product_name": "nom du produit en français",
    "brand": "marque en français",
    "description": "description courte en français"
}}

Texte: {text[:2000]}

JSON en français:"""

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": simple_prompt,
                        "stream": False,
                        "options": {"temperature": 0.1}
                    }
                )
                response.raise_for_status()
                result = response.json()
                
                json_str = self.extract_json_from_text(result["response"])
                parsed_json = json.loads(json_str)
                
                # Créer une structure complète avec les données disponibles
                validated_data = self.create_fallback_structure(parsed_json)
                
                # Sauvegarder la réponse du modèle si session_id et output_path sont fournis
                if session_id and output_path:
                    await self.save_model_response(session_id, simple_prompt, json_str, validated_data, output_path)
                
                return validated_data
                
        except Exception as e:
            logger.error(f"Erreur avec le prompt simplifié: {str(e)}")
            fallback_data = self.create_fallback_structure({})
            
            # Sauvegarder même en cas d'erreur si session_id et output_path sont fournis
            if session_id and output_path:
                await self.save_model_response(session_id, simple_prompt, "Erreur lors de l'analyse", fallback_data, output_path)
            
            return fallback_data

    def create_fallback_structure(self, partial_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Crée une structure complète avec des données partielles"""
        if partial_data is None:
            partial_data = {}
            
        return {
            "product_name": partial_data.get("product_name", ""),
            "brand": partial_data.get("brand", ""),
            "model_number": partial_data.get("model_number", ""),
            "category": partial_data.get("category", ""),
            "description": partial_data.get("description", ""),
            "price_range": partial_data.get("price_range", ""),
            "technical_specs": partial_data.get("technical_specs", {}),
            "dimensions": partial_data.get("dimensions", {}),
            "weight": partial_data.get("weight", ""),
            "features": partial_data.get("features", []),
            "certifications": partial_data.get("certifications", []),
            "warranty": partial_data.get("warranty", ""),
            "installation_requirements": partial_data.get("installation_requirements", ""),
            "maintenance": partial_data.get("maintenance", ""),
            "safety_features": partial_data.get("safety_features", ""),
            "accessories_included": partial_data.get("accessories_included", ""),
            "compatibility": partial_data.get("compatibility", ""),
            "environmental_conditions": partial_data.get("environmental_conditions", ""),
            "standards_compliance": partial_data.get("standards_compliance", ""),
            "additional_info": partial_data.get("additional_info", "")
        }

    def split_text(self, text: str, max_length: int = 4000) -> list:
        """Découpe le texte en segments avec chevauchement"""
        if len(text) <= max_length:
            return [text]
        
        segments = []
        overlap = 200  # Chevauchement entre segments
        start = 0
        
        while start < len(text):
            end = start + max_length
            
            if end >= len(text):
                segments.append(text[start:])
                break
            
            # Chercher un point de coupure naturel
            cut_point = text.rfind('\n', start, end)
            if cut_point == -1:
                cut_point = text.rfind('.', start, end)
            if cut_point == -1:
                cut_point = text.rfind(' ', start, end)
            if cut_point == -1:
                cut_point = end
            
            segments.append(text[start:cut_point])
            start = max(cut_point - overlap, start + 1)
        
        return segments

    def merge_results(self, results: list) -> dict:
        """Fusionne les résultats JSON extraits de chaque segment"""
        if not results:
            return self.create_fallback_structure()
        
        if len(results) == 1:
            return results[0]
        
        merged = self.create_fallback_structure()
        
        for res in results:
            for key, value in res.items():
                if not value:  # Ignorer les valeurs vides
                    continue
                    
                current_value = merged[key]
                
                # Si les deux valeurs sont des dictionnaires
                if isinstance(value, dict) and isinstance(current_value, dict):
                    for subkey, subval in value.items():
                        if subval and (not current_value.get(subkey) or len(str(subval)) > len(str(current_value[subkey]))):
                            current_value[subkey] = subval
                
                # Si les deux valeurs sont des listes
                elif isinstance(value, list) and isinstance(current_value, list):
                    # Fusionner les listes en évitant les doublons
                    merged[key] = list(set(current_value + value))
                
                # Si les deux valeurs sont des chaînes
                elif isinstance(value, str) and isinstance(current_value, str):
                    # Prendre la plus longue chaîne non vide
                    if value and (not current_value or len(value) > len(current_value)):
                        merged[key] = value
        
        return merged

    async def analyze_pdf(self, pdf_path: Path, session_id: str = None, output_path: Path = None) -> Dict[str, Any]:
        """Analyse complète d'un fichier PDF"""
        logger.info(f"=== DÉBUT ANALYSE PDF: {pdf_path} ===")
        
        try:
            # Vérification de la disponibilité d'Ollama
            if not await self.wait_for_ollama():
                raise Exception("Ollama n'est pas disponible")
            
            # Extraction du texte
            text = self.extract_text_from_pdf(pdf_path)
            
            # Détection du type de produit
            product_type = self.detect_product_type(text)
            
            # Si le texte est court, analyser directement
            if len(text) <= 4000:
                result = await self.analyze_with_ollama(text, session_id, output_path)
            else:
                # Découpage en segments
                segments = self.split_text(text, 4000)
                logger.info(f"Texte découpé en {len(segments)} segments")
                
                # Analyse de chaque segment
                results = []
                for idx, segment in enumerate(segments):
                    logger.info(f"Analyse du segment {idx+1}/{len(segments)}")
                    res = await self.analyze_with_ollama(segment, session_id, output_path)
                    results.append(res)
                
                # Fusion des résultats
                result = self.merge_results(results)
            
            logger.info("=== FIN ANALYSE PDF ===")
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse: {e}")
            raise