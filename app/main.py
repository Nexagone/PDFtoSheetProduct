import os
import tempfile
from typing import Dict, List
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from .services.pdf_processor import PDFProcessor
from .services.ai_analyzer import AIAnalyzer
from .models.product import ProductSheet

# Configuration des logs
logger.add("app.log", rotation="500 MB")

app = FastAPI(
    title="PDF Product Sheet Extractor",
    description="API pour extraire des fiches produit depuis des PDFs",
    version="1.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialisation des services
pdf_processor = PDFProcessor()
ai_analyzer = AIAnalyzer(
    ollama_url=os.getenv("OLLAMA_URL", "http://ollama:11434")
)

@app.post("/analyze-pdf", response_model=ProductSheet)
async def analyze_pdf(file: UploadFile = File(...)):
    """
    Analyse un fichier PDF et extrait les informations produit.
    
    Args:
        file: Fichier PDF à analyser
        
    Returns:
        Fiche produit structurée
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Le fichier doit être au format PDF"
        )

    try:
        # Sauvegarde temporaire du fichier
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        try:
            # Extraction du contenu
            images, text = await pdf_processor.process_pdf(temp_file_path)
            
            # Récupération des métadonnées
            metadata = pdf_processor.get_metadata(temp_file_path)
            
            # Optimisation des images
            optimized_images = [
                pdf_processor.optimize_image(img)
                for img in images
            ]
            
            # Analyse du contenu
            product_sheet = await ai_analyzer.analyze_content(
                optimized_images,
                text,
                metadata
            )
            
            return product_sheet

        finally:
            # Nettoyage du fichier temporaire
            os.unlink(temp_file_path)

    except Exception as e:
        logger.error(f"Erreur lors de l'analyse du PDF: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'analyse du PDF: {str(e)}"
        )

@app.post("/analyze-text", response_model=ProductSheet)
async def analyze_text(text: str):
    """
    Analyse un texte brut pour extraire les informations produit.
    
    Args:
        text: Texte à analyser
        
    Returns:
        Fiche produit structurée
    """
    try:
        product_sheet = await ai_analyzer.analyze_content(
            images=[],
            text=text,
            metadata={}
        )
        return product_sheet
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse du texte: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'analyse du texte: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """
    Vérifie l'état de santé de l'API et des services.
    
    Returns:
        État de santé des différents composants
    """
    ollama_status = await ai_analyzer.health_check()
    
    return {
        "status": "healthy" if ollama_status else "degraded",
        "services": {
            "api": "up",
            "ollama": "up" if ollama_status else "down"
        }
    }

@app.get("/models")
async def list_models():
    """
    Liste les modèles disponibles.
    
    Returns:
        Liste des modèles configurés
    """
    return {
        "current_model": ai_analyzer.model,
        "supported_models": [
            {
                "name": "llama3.2-vision:11b",
                "type": "vision",
                "description": "Modèle multimodal pour l'analyse de documents"
            }
        ]
    } 