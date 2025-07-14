#!/usr/bin/env python3
"""
Script pour visualiser les réponses du modèle sauvegardées dans le dossier outputs
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

def load_model_responses(outputs_dir: str = "outputs") -> List[Dict[str, Any]]:
    """Charge toutes les réponses du modèle depuis le dossier outputs"""
    responses = []
    outputs_path = Path(outputs_dir)
    
    if not outputs_path.exists():
        print(f"❌ Le dossier {outputs_dir} n'existe pas")
        return responses
    
    # Chercher dans tous les sous-dossiers
    for session_dir in outputs_path.iterdir():
        if session_dir.is_dir():
            model_responses_dir = session_dir / "model_responses"
            if model_responses_dir.exists():
                for json_file in model_responses_dir.glob("*.json"):
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            data['file_path'] = str(json_file)
                            responses.append(data)
                    except Exception as e:
                        print(f"⚠️  Erreur lors du chargement de {json_file}: {e}")
    
    return responses

def display_response_summary(response: Dict[str, Any]) -> None:
    """Affiche un résumé d'une réponse"""
    metadata = response.get('metadata', {})
    analysis_info = response.get('analysis_info', {})
    
    print(f"📄 Session: {metadata.get('session_id', 'N/A')}")
    print(f"🕒 Timestamp: {metadata.get('timestamp', 'N/A')}")
    print(f"🤖 Modèle: {metadata.get('model', 'N/A')}")
    print(f"📏 Longueur prompt: {analysis_info.get('prompt_length', 0)} caractères")
    print(f"📏 Longueur réponse: {analysis_info.get('response_length', 0)} caractères")
    print(f"📊 Champs extraits: {analysis_info.get('parsed_fields_count', 0)}")
    
    # Afficher les données extraites principales
    parsed_data = response.get('parsed_data', {})
    if parsed_data:
        print(f"🏷️  Nom produit: {parsed_data.get('product_name', 'N/A')}")
        print(f"🏭 Marque: {parsed_data.get('brand', 'N/A')}")
        print(f"📋 Description: {parsed_data.get('description', 'N/A')[:100]}...")
    
    print("-" * 50)

def display_detailed_response(response: Dict[str, Any]) -> None:
    """Affiche une réponse détaillée"""
    print("=" * 80)
    print("📋 RÉPONSE DÉTAILLÉE DU MODÈLE")
    print("=" * 80)
    
    # Métadonnées
    metadata = response.get('metadata', {})
    print(f"📄 Fichier: {response.get('file_path', 'N/A')}")
    print(f"🕒 Session: {metadata.get('session_id', 'N/A')}")
    print(f"🕒 Timestamp: {metadata.get('timestamp', 'N/A')}")
    print(f"🤖 Modèle: {metadata.get('model', 'N/A')}")
    
    # Informations d'analyse
    analysis_info = response.get('analysis_info', {})
    print(f"\n📊 INFORMATIONS D'ANALYSE:")
    print(f"   - Longueur prompt: {analysis_info.get('prompt_length', 0)} caractères")
    print(f"   - Longueur réponse: {analysis_info.get('response_length', 0)} caractères")
    print(f"   - Champs extraits: {analysis_info.get('parsed_fields_count', 0)}")
    
    # Prompt (tronqué)
    prompt = response.get('prompt', '')
    if prompt:
        print(f"\n🤖 PROMPT (premiers 200 caractères):")
        print(f"   {prompt[:200]}...")
    
    # Réponse brute (tronquée)
    raw_response = response.get('raw_response', '')
    if raw_response:
        print(f"\n📝 RÉPONSE BRUTE (premiers 300 caractères):")
        print(f"   {raw_response[:300]}...")
    
    # Données parsées
    parsed_data = response.get('parsed_data', {})
    if parsed_data:
        print(f"\n✅ DONNÉES EXTRACTES:")
        for key, value in parsed_data.items():
            if value:  # Afficher seulement les champs non vides
                if isinstance(value, dict):
                    print(f"   {key}:")
                    for subkey, subvalue in value.items():
                        if subvalue:
                            print(f"     - {subkey}: {subvalue}")
                elif isinstance(value, list):
                    print(f"   {key}: {', '.join(str(v) for v in value[:3])}")
                    if len(value) > 3:
                        print(f"     ... et {len(value) - 3} autres")
                else:
                    print(f"   {key}: {value}")
    
    print("=" * 80)

def main():
    """Fonction principale"""
    print("🔍 VISUALISATEUR DES RÉPONSES DU MODÈLE")
    print("=" * 50)
    
    # Charger les réponses
    responses = load_model_responses()
    
    if not responses:
        print("❌ Aucune réponse du modèle trouvée")
        print("💡 Assurez-vous d'avoir traité au moins un PDF")
        return
    
    print(f"✅ {len(responses)} réponse(s) trouvée(s)")
    print()
    
    # Afficher le résumé de toutes les réponses
    print("📋 RÉSUMÉ DES RÉPONSES:")
    print("-" * 50)
    for i, response in enumerate(responses, 1):
        print(f"\n{i}. ", end="")
        display_response_summary(response)
    
    # Demander quelle réponse afficher en détail
    if len(responses) > 1:
        try:
            choice = input(f"\n🔍 Entrez le numéro de la réponse à afficher en détail (1-{len(responses)}) ou 'q' pour quitter: ")
            if choice.lower() == 'q':
                return
            
            choice_num = int(choice)
            if 1 <= choice_num <= len(responses):
                display_detailed_response(responses[choice_num - 1])
            else:
                print("❌ Numéro invalide")
        except ValueError:
            print("❌ Entrée invalide")
    else:
        # Si une seule réponse, l'afficher directement
        display_detailed_response(responses[0])

if __name__ == "__main__":
    main() 