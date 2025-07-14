#!/usr/bin/env python3
"""
Script pour nettoyer les anciennes réponses du modèle
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List

def cleanup_old_responses(outputs_dir: str = "outputs", days_to_keep: int = 7) -> None:
    """Nettoie les anciennes réponses du modèle"""
    outputs_path = Path(outputs_dir)
    
    if not outputs_path.exists():
        print(f"❌ Le dossier {outputs_dir} n'existe pas")
        return
    
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    deleted_count = 0
    
    print(f"🧹 Nettoyage des réponses plus anciennes que {days_to_keep} jours...")
    print(f"📅 Date limite: {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Parcourir tous les sous-dossiers
    for session_dir in outputs_path.iterdir():
        if session_dir.is_dir():
            model_responses_dir = session_dir / "model_responses"
            if model_responses_dir.exists():
                for json_file in model_responses_dir.glob("*.json"):
                    try:
                        # Vérifier la date de modification du fichier
                        file_mtime = datetime.fromtimestamp(json_file.stat().st_mtime)
                        
                        if file_mtime < cutoff_date:
                            print(f"🗑️  Suppression: {json_file}")
                            json_file.unlink()
                            deleted_count += 1
                            
                            # Si le dossier est vide, le supprimer aussi
                            if not any(model_responses_dir.iterdir()):
                                model_responses_dir.rmdir()
                                print(f"🗑️  Suppression du dossier vide: {model_responses_dir}")
                                
                    except Exception as e:
                        print(f"⚠️  Erreur lors de la suppression de {json_file}: {e}")
    
    print(f"\n✅ Nettoyage terminé: {deleted_count} fichier(s) supprimé(s)")

def list_responses_by_age(outputs_dir: str = "outputs") -> None:
    """Liste les réponses par âge"""
    outputs_path = Path(outputs_dir)
    
    if not outputs_path.exists():
        print(f"❌ Le dossier {outputs_dir} n'existe pas")
        return
    
    responses = []
    
    # Parcourir tous les sous-dossiers
    for session_dir in outputs_path.iterdir():
        if session_dir.is_dir():
            model_responses_dir = session_dir / "model_responses"
            if model_responses_dir.exists():
                for json_file in model_responses_dir.glob("*.json"):
                    try:
                        file_mtime = datetime.fromtimestamp(json_file.stat().st_mtime)
                        age_days = (datetime.now() - file_mtime).days
                        
                        responses.append({
                            'file': json_file,
                            'age_days': age_days,
                            'mtime': file_mtime
                        })
                    except Exception as e:
                        print(f"⚠️  Erreur lors de l'analyse de {json_file}: {e}")
    
    if not responses:
        print("❌ Aucune réponse trouvée")
        return
    
    # Trier par âge
    responses.sort(key=lambda x: x['age_days'], reverse=True)
    
    print(f"📋 {len(responses)} réponse(s) trouvée(s):")
    print("-" * 80)
    
    for i, response in enumerate(responses, 1):
        age = response['age_days']
        age_str = f"{age} jour(s)" if age > 0 else "Aujourd'hui"
        
        print(f"{i:2d}. {response['file'].name}")
        print(f"    Âge: {age_str}")
        print(f"    Date: {response['mtime'].strftime('%Y-%m-%d %H:%M:%S')}")
        print()

def main():
    """Fonction principale"""
    print("🧹 NETTOYEUR DES RÉPONSES DU MODÈLE")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "clean":
            days = 7
            if len(sys.argv) > 2:
                try:
                    days = int(sys.argv[2])
                except ValueError:
                    print("❌ Nombre de jours invalide")
                    return
            
            cleanup_old_responses(days_to_keep=days)
            
        elif command == "list":
            list_responses_by_age()
            
        else:
            print("❌ Commande invalide")
            print("Usage:")
            print("  python cleanup-model-responses.py clean [jours]  # Nettoyer les anciennes réponses")
            print("  python cleanup-model-responses.py list            # Lister les réponses par âge")
    else:
        # Mode interactif
        print("Choisissez une action:")
        print("1. Lister les réponses par âge")
        print("2. Nettoyer les anciennes réponses")
        print("3. Quitter")
        
        try:
            choice = input("\nVotre choix (1-3): ")
            
            if choice == "1":
                list_responses_by_age()
            elif choice == "2":
                try:
                    days = int(input("Nombre de jours à conserver (défaut: 7): ") or "7")
                    cleanup_old_responses(days_to_keep=days)
                except ValueError:
                    print("❌ Nombre de jours invalide")
            elif choice == "3":
                print("👋 Au revoir!")
            else:
                print("❌ Choix invalide")
        except KeyboardInterrupt:
            print("\n👋 Au revoir!")

if __name__ == "__main__":
    main() 