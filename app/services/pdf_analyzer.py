import PyPDF2
import io
import httpx
import json
import asyncio
import logging
import re
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
            print(f"=== DEBUG PDF === Début de l'extraction du texte du PDF: {pdf_path}", flush=True)
            
            logger.info(f"Taille du fichier PDF: {pdf_path.stat().st_size} octets")
            print(f"=== DEBUG PDF === Taille du fichier PDF: {pdf_path.stat().st_size} octets", flush=True)
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                logger.info(f"Nombre de pages dans le PDF: {len(pdf_reader.pages)}")
                print(f"=== DEBUG PDF === Nombre de pages dans le PDF: {len(pdf_reader.pages)}", flush=True)
                
                text = ""
                for i, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    text += page_text
                    logger.info(f"Page {i+1} extraite, longueur: {len(page_text)} caractères")
                    print(f"=== DEBUG PDF === Page {i+1} extraite, longueur: {len(page_text)} caractères", flush=True)
                    logger.info(f"Contenu de la page {i+1} (premiers 200 caractères): {page_text[:200]}")
                    print(f"=== DEBUG PDF === Contenu de la page {i+1} (premiers 200 caractères): {page_text[:200]}", flush=True)
                
                # Limiter la taille du texte pour éviter le troncage du prompt
                max_text_length = 3000  # Limite pour laisser de la place au prompt
                if len(text) > max_text_length:
                    logger.warning(f"Texte tronqué de {len(text)} à {max_text_length} caractères")
                    print(f"=== DEBUG PDF === Texte tronqué de {len(text)} à {max_text_length} caractères", flush=True)
                    text = text[:max_text_length] + "..."
                
                logger.info(f"Extraction terminée, texte total: {len(text)} caractères")
                print(f"=== DEBUG PDF === Extraction terminée, texte total: {len(text)} caractères", flush=True)
                logger.info(f"Texte extrait (premiers 500 caractères): {text[:500]}")
                print(f"=== DEBUG PDF === Texte extrait (premiers 500 caractères): {text[:500]}", flush=True)
                return text
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction du PDF: {str(e)}", exc_info=True)
            print(f"=== DEBUG PDF === Erreur lors de l'extraction du PDF: {str(e)}", flush=True)
            raise Exception(f"Erreur lors de l'extraction du PDF: {str(e)}")

    def extract_json_from_text(self, text: str) -> str:
        """Extrait le JSON de la réponse d'Ollama avec plusieurs méthodes"""
        # Méthode 1: Recherche directe de JSON
        start = text.find('{')
        end = text.rfind('}') + 1
        if start != -1 and end > start:
            json_candidate = text[start:end]
            try:
                json.loads(json_candidate)
                return json_candidate
            except json.JSONDecodeError:
                pass
        
        # Méthode 2: Recherche avec regex pour JSON mal formaté
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)
        if matches:
            for match in matches:
                try:
                    json.loads(match)
                    return match
                except json.JSONDecodeError:
                    continue
        
        # Méthode 3: Essayer de nettoyer et reformater
        cleaned_text = re.sub(r'[^\x20-\x7E]', '', text)  # Supprimer caractères non-ASCII
        start = cleaned_text.find('{')
        end = cleaned_text.rfind('}') + 1
        if start != -1 and end > start:
            return cleaned_text[start:end]
        
        raise ValueError("Aucun JSON valide trouvé dans la réponse")

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

    def create_structured_prompt(self, text: str) -> str:
        """Crée un prompt structuré pour l'analyse du texte"""
        prompt = f"""Tu es un expert en analyse de fiches techniques produits. Tu dois analyser EXCLUSIVEMENT le texte fourni ci-dessous et extraire UNIQUEMENT les informations qui y sont explicitement mentionnées.

⚠️ RÈGLE ABSOLUE : Ne jamais inventer ou deviner d'informations. Si une information n'est pas dans le texte, mets une chaîne vide "".

TEXTE À ANALYSER (analyse uniquement ce contenu) :
{text}

INSTRUCTIONS STRICTES :
1. Analyse UNIQUEMENT le texte fourni ci-dessus
2. Ne fais AUCUNE supposition ou déduction
3. Si une information n'est pas explicitement dans le texte, mets ""
4. Pour chaque champ, cherche EXACTEMENT les mots-clés dans le texte
5. Ne génère JAMAIS de contenu qui n'est pas dans le texte fourni
6. Si le document fourni est dans une langue autre que le français, réponds en français.

FORMAT DE RÉPONSE OBLIGATOIRE (JSON valide) :
{{
    "product_name": "Nom exact trouvé dans le texte (ou chaîne vide si pas trouvé)",
    "brand": "Marque exacte trouvée dans le texte (ou chaîne vide si pas trouvé)",
    "model": "Modèle/référence exact trouvé dans le texte (ou chaîne vide si pas trouvé)",
    "category": "Catégorie exacte trouvée dans le texte (ou chaîne vide si pas trouvé)",
    "description": "Description exacte trouvée dans le texte (ou chaîne vide si pas trouvé)",
    "technical_specifications": {{
        "dimensions": "Dimensions exactes trouvées (mm, cm, m, x, ×)",
        "weight": "Poids exact trouvé (kg, g, poids)",
        "power": "Puissance exacte trouvée (W, watts, puissance)",
        "voltage": "Tension exacte trouvée (V, volts, tension)",
        "frequency": "Fréquence exacte trouvée (Hz, hertz, fréquence)",
        "capacity": "Capacité/volume exact trouvé",
        "efficiency": "Classe énergétique exacte trouvée",
        "noise_level": "Niveau sonore exact trouvé (dB, décibels, sonore)"
    }},
    "features": [
        "Fonctionnalité 1 trouvée dans le texte",
        "Fonctionnalité 2 trouvée dans le texte"
    ],
    "materials": "Matériaux exacts trouvés dans le texte",
    "warranty": "Garantie exacte trouvée dans le texte",
    "certifications": "Certifications exactes trouvées dans le texte",
    "installation_requirements": "Exigences d'installation exactes trouvées",
    "maintenance": "Instructions de maintenance exactes trouvées",
    "safety_features": "Fonctionnalités de sécurité exactes trouvées",
    "additional_info": "Autres informations exactes trouvées dans le texte"
}}

RÈGLES DE RECHERCHE PRÉCISES :
- Cherche EXACTEMENT ces mots-clés dans le texte : "mm", "cm", "m", "x", "×", "kg", "g", "poids", "W", "watts", "puissance", "V", "volts", "tension", "Hz", "hertz", "fréquence", "dB", "décibels", "sonore"
- Si tu ne trouves PAS l'information dans le texte, mets ""
- Ne génère JAMAIS de contenu qui n'est pas explicitement dans le texte fourni

RÉPONDS UNIQUEMENT AVEC LE JSON, SANS COMMENTAIRES NI EXPLICATIONS."""
        return prompt

    async def analyze_with_ollama(self, text: str) -> Dict[str, Any]:
        """Analyse le texte avec Ollama pour extraire les informations produit"""
        logger.info(f"Début de l'analyse avec Ollama, texte à analyser: {len(text)} caractères")
        print(f"=== DEBUG OLLAMA === Début de l'analyse avec Ollama, texte à analyser: {len(text)} caractères", flush=True)
        
        logger.info(f"Premiers 300 caractères du texte: {text[:300]}")
        print(f"=== DEBUG OLLAMA === Premiers 300 caractères du texte: {text[:300]}", flush=True)
        
        prompt = self.create_structured_prompt(text)
        logger.info(f"Prompt créé, longueur: {len(prompt)} caractères")
        print(f"=== DEBUG OLLAMA === Prompt créé, longueur: {len(prompt)} caractères", flush=True)
        logger.info(f"Prompt complet: {prompt}")
        print(f"=== DEBUG OLLAMA === Prompt complet: {prompt}", flush=True)

        retries = 0
        while retries < self.max_retries:
            try:
                logger.info(f"Tentative {retries + 1}/{self.max_retries} d'analyse avec Ollama")
                print(f"=== DEBUG OLLAMA === Tentative {retries + 1}/{self.max_retries} d'analyse avec Ollama", flush=True)
                
                logger.info(f"URL Ollama: {self.ollama_url}")
                print(f"=== DEBUG OLLAMA === URL Ollama: {self.ollama_url}", flush=True)
                
                logger.info(f"Modèle utilisé: {self.model}")
                print(f"=== DEBUG OLLAMA === Modèle utilisé: {self.model}", flush=True)
                
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    logger.info("Envoi de la requête à Ollama")
                    print("=== DEBUG OLLAMA === Envoi de la requête à Ollama", flush=True)
                    
                    request_data = {
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.1,  # Réponses plus cohérentes
                            "top_p": 0.9,
                            "num_predict": 2048
                        }
                    }
                    logger.info(f"Données de la requête: {request_data}")
                    print(f"=== DEBUG OLLAMA === Données de la requête: {request_data}", flush=True)
                    
                    response = await client.post(
                        f"{self.ollama_url}/api/generate",
                        json=request_data
                    )
                    response.raise_for_status()
                    result = response.json()
                    logger.info("Réponse reçue d'Ollama")
                    print("=== DEBUG OLLAMA === Réponse reçue d'Ollama", flush=True)
                    
                    logger.info(f"Réponse complète d'Ollama: {result}")
                    print(f"=== DEBUG OLLAMA === Réponse complète d'Ollama: {result}", flush=True)
                    
                    try:
                        json_str = result["response"]
                        logger.info(f"Réponse brute d'Ollama: {json_str}")
                        print(f"=== DEBUG OLLAMA === Réponse brute d'Ollama: {json_str}", flush=True)
                        
                        # Utilisation de la nouvelle fonction de parsing
                        data = self.parse_json_response(json_str)
                        logger.info(f"Données extraites: {data}")
                        print(f"=== DEBUG OLLAMA === Données extraites: {data}", flush=True)
                        
                        return data
                    except Exception as e:
                        logger.error(f"Erreur lors du parsing: {str(e)}", exc_info=True)
                        print(f"=== DEBUG OLLAMA === Erreur lors du parsing: {str(e)}", flush=True)
                        
                        # Si c'est la dernière tentative, essayer avec un prompt simplifié
                        if retries == self.max_retries - 1:
                            logger.info("Tentative avec un prompt simplifié...")
                            print("=== DEBUG OLLAMA === Tentative avec un prompt simplifié...", flush=True)
                            return await self.analyze_with_simple_prompt(text)
                        
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

    async def analyze_with_simple_prompt(self, text: str) -> Dict[str, Any]:
        """Analyse avec un prompt simplifié en cas d'échec"""
        simple_prompt = f"""Extrait les informations produit de ce texte et réponds avec un JSON simple:
{{
    "product_name": "nom du produit",
    "brand": "marque",
    "description": "description courte"
}}

Texte: {text}

JSON:"""

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": simple_prompt,
                        "stream": False
                    }
                )
                response.raise_for_status()
                result = response.json()
                
                json_str = self.extract_json_from_text(result["response"])
                parsed_json = json.loads(json_str)
                
                # Créer une structure complète avec les données disponibles
                full_structure = {
                    "product_name": parsed_json.get("product_name", ""),
                    "brand": parsed_json.get("brand", ""),
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
                    "description": parsed_json.get("description", ""),
                    "color": "",
                    "material": "",
                    "certifications": []
                }
                
                return self.format_json_response(full_structure)
        except Exception as e:
            logger.error(f"Erreur avec le prompt simplifié: {str(e)}")
            # Retourner une structure vide en cas d'échec total
            return {
                "product_name": "",
                "brand": "",
                "model_number": "",
                "category": "",
                "technical_specs": {"volume": "", "classe_energetique": "", "capacite": "", "puissance": "", "tension": "", "frequence": ""},
                "dimensions": {"longueur": "", "largeur": "", "hauteur": "", "profondeur": ""},
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

    def parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Parse la réponse JSON d'Ollama"""
        logger.info(f"Parsing de la réponse JSON, longueur: {len(response_text)}")
        print(f"=== DEBUG JSON === Parsing de la réponse JSON, longueur: {len(response_text)}", flush=True)
        
        # Nettoyage de la réponse
        cleaned_response = response_text.strip()
        
        # Suppression des balises markdown si présentes
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]
        cleaned_response = cleaned_response.strip()
        
        logger.info(f"Réponse nettoyée: {cleaned_response[:200]}...")
        print(f"=== DEBUG JSON === Réponse nettoyée: {cleaned_response[:200]}...", flush=True)
        
        try:
            # Tentative de parsing direct
            data = json.loads(cleaned_response)
            logger.info("JSON parsé avec succès")
            print("=== DEBUG JSON === JSON parsé avec succès", flush=True)
            return data
        except json.JSONDecodeError as e:
            logger.warning(f"Erreur de parsing JSON: {e}")
            print(f"=== DEBUG JSON === Erreur de parsing JSON: {e}", flush=True)
            
            # Tentative de récupération du JSON avec regex
            import re
            json_pattern = r'\{.*\}'
            json_match = re.search(json_pattern, cleaned_response, re.DOTALL)
            
            if json_match:
                try:
                    json_str = json_match.group(0)
                    data = json.loads(json_str)
                    logger.info("JSON récupéré avec regex et parsé avec succès")
                    print("=== DEBUG JSON === JSON récupéré avec regex et parsé avec succès", flush=True)
                    return data
                except json.JSONDecodeError as e2:
                    logger.error(f"Échec du parsing avec regex: {e2}")
                    print(f"=== DEBUG JSON === Échec du parsing avec regex: {e2}", flush=True)
            
            # Fallback: retourner un JSON vide avec la réponse brute
            logger.error("Impossible de parser le JSON, utilisation du fallback")
            print("=== DEBUG JSON === Impossible de parser le JSON, utilisation du fallback", flush=True)
            return {
                "error": "Impossible de parser la réponse JSON",
                "raw_response": cleaned_response[:500],
                "product_name": "",
                "brand": "",
                "model": "",
                "category": "",
                "description": "",
                "technical_specifications": {
                    "dimensions": "",
                    "weight": "",
                    "power": "",
                    "voltage": "",
                    "frequency": "",
                    "capacity": "",
                    "efficiency": "",
                    "noise_level": ""
                },
                "features": [],
                "materials": "",
                "warranty": "",
                "certifications": "",
                "installation_requirements": "",
                "maintenance": "",
                "safety_features": "",
                "additional_info": ""
            }

    def split_text(self, text: str, max_length: int = 3000) -> list:
        """Découpe le texte en segments de taille max_length"""
        return [text[i:i+max_length] for i in range(0, len(text), max_length)]

    def merge_results(self, results: list) -> dict:
        """Fusionne les résultats JSON extraits de chaque segment"""
        # On part du premier résultat comme base
        if not results:
            return {}
        merged = results[0].copy()
        
        for res in results[1:]:
            for key, value in res.items():
                if key not in merged:
                    merged[key] = value
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
                
                # Si les types sont différents, prendre la valeur non vide la plus complète
                else:
                    if value and (not current_value or len(str(value)) > len(str(current_value))):
                        merged[key] = value
        
        return merged

    async def analyze_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """Analyse complète d'un fichier PDF (multi-segments)"""
        logger.info(f"=== DÉBUT ANALYSE PDF ===")
        print("=== DEBUG ANALYSE === DÉBUT ANALYSE PDF", flush=True)
        
        logger.info(f"Fichier PDF à analyser: {pdf_path}")
        print(f"=== DEBUG ANALYSE === Fichier PDF à analyser: {pdf_path}", flush=True)
        
        logger.info(f"Fichier existe: {pdf_path.exists()}")
        print(f"=== DEBUG ANALYSE === Fichier existe: {pdf_path.exists()}", flush=True)
        
        # Vérification de la disponibilité d'Ollama
        logger.info("Vérification de la disponibilité d'Ollama...")
        print("=== DEBUG ANALYSE === Vérification de la disponibilité d'Ollama...", flush=True)
        if not await self.wait_for_ollama():
            logger.error("Ollama n'est pas disponible")
            print("=== DEBUG ANALYSE === Ollama n'est pas disponible", flush=True)
            raise Exception("Ollama n'est pas disponible")
        
        # Extraction du texte
        logger.info("Début de l'extraction du texte...")
        print("=== DEBUG ANALYSE === Début de l'extraction du texte...", flush=True)
        text = self.extract_text_from_pdf(pdf_path)
        logger.info(f"Texte extrait avec succès, longueur: {len(text)} caractères")
        print(f"=== DEBUG ANALYSE === Texte extrait avec succès, longueur: {len(text)} caractères", flush=True)
        
        # Découpage en segments
        segments = self.split_text(text, 3000)
        logger.info(f"Texte découpé en {len(segments)} segments de 3000 caractères max")
        print(f"=== DEBUG ANALYSE === Texte découpé en {len(segments)} segments", flush=True)
        
        # Analyse chaque segment
        results = []
        for idx, segment in enumerate(segments):
            logger.info(f"Analyse du segment {idx+1}/{len(segments)}")
            print(f"=== DEBUG ANALYSE === Analyse du segment {idx+1}/{len(segments)}", flush=True)
            res = await self.analyze_with_ollama(segment)
            results.append(res)
        
        # Fusion des résultats
        merged = self.merge_results(results)
        logger.info(f"Analyse terminée, données fusionnées: {merged}")
        print(f"=== DEBUG ANALYSE === Analyse terminée, données fusionnées: {merged}", flush=True)
        
        # Validation et nettoyage des hallucinations
        validated_data = self.validate_and_clean_response(merged, text)
        
        logger.info("=== FIN ANALYSE PDF ===")
        print("=== DEBUG ANALYSE === FIN ANALYSE PDF", flush=True)
        return validated_data 

    def validate_and_clean_response(self, data: dict, original_text: str) -> dict:
        """Valide et nettoie la réponse pour éviter les hallucinations"""
        logger.info("Validation de la réponse pour éviter les hallucinations")
        print("=== DEBUG VALIDATION === Validation de la réponse", flush=True)
        
        # Liste des termes hallucinés courants à détecter
        hallucination_terms = [
            "Fournisseur de chaleur à inertie",
            "HTR 3000",
            "système de chauffage à inertie",
            "applications industrielles",
            "applications commerciales"
        ]
        
        cleaned_data = data.copy()
        
        # Vérifier chaque champ pour détecter les hallucinations
        for key, value in cleaned_data.items():
            if isinstance(value, str) and value:
                # Vérifier si la valeur contient des termes hallucinés
                for term in hallucination_terms:
                    if term.lower() in value.lower():
                        logger.warning(f"Hallucination détectée dans {key}: {value}")
                        print(f"=== DEBUG VALIDATION === Hallucination détectée dans {key}: {value}", flush=True)
                        # Vérifier si le terme existe vraiment dans le texte original
                        if term.lower() not in original_text.lower():
                            cleaned_data[key] = ""
                            logger.info(f"Champ {key} vidé car hallucination détectée")
                            print(f"=== DEBUG VALIDATION === Champ {key} vidé", flush=True)
                            break
            
            elif isinstance(value, list):
                # Vérifier chaque élément de la liste
                cleaned_list = []
                for item in value:
                    is_hallucination = False
                    for term in hallucination_terms:
                        if term.lower() in item.lower() and term.lower() not in original_text.lower():
                            is_hallucination = True
                            break
                    if not is_hallucination:
                        cleaned_list.append(item)
                cleaned_data[key] = cleaned_list
        
        logger.info(f"Données validées: {cleaned_data}")
        print(f"=== DEBUG VALIDATION === Données validées: {cleaned_data}", flush=True)
        return cleaned_data 