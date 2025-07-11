from fastapi import FastAPI, UploadFile, HTTPException, Form
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
import os
import uuid
import aiofiles
from pathlib import Path
from typing import Optional
import logging

from app.services.pdf_analyzer import PDFAnalyzer
from app.services.html_generator import HTMLGenerator
from app.services.pdf_generator import PDFGenerator
from app.config import settings

# Configuration des logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Générateur de Fiches Produit",
    description="Service de génération de fiches produit HTML/PDF à partir de PDF constructeur",
    version="1.0.0"
)

# Montage des fichiers statiques
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Configuration des templates
templates = Jinja2Templates(directory="app/templates")

# Création des dossiers nécessaires
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.OUTPUT_DIR, exist_ok=True)

def cleanup_outputs():
    """Nettoie le dossier outputs au démarrage"""
    try:
        import shutil
        if os.path.exists(settings.OUTPUT_DIR):
            shutil.rmtree(settings.OUTPUT_DIR)
        os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
        logger.info("Dossier outputs nettoyé au démarrage")
    except Exception as e:
        logger.warning(f"Impossible de nettoyer le dossier outputs: {e}")

# Nettoyage au démarrage
cleanup_outputs()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Page d'accueil avec interface drag & drop"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload")
async def upload_pdf(
    file: UploadFile,
    output_format: str = Form("html"),
    output_dir: Optional[str] = Form(None)
):
    """
    Endpoint pour l'upload et le traitement d'un fichier PDF
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Le fichier doit être un PDF")
    
    # Génération d'un ID unique pour cette session
    session_id = str(uuid.uuid4())
    
    try:
        # Lecture du fichier
        content = await file.read()
        
        # Création du dossier de sortie personnalisé si spécifié
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
        else:
            output_path = Path(settings.OUTPUT_DIR) / session_id
            output_path.mkdir(parents=True, exist_ok=True)
        
        # Sauvegarde du fichier PDF original
        pdf_path = Path(settings.UPLOAD_DIR) / f"{session_id}_{file.filename}"
        async with aiofiles.open(pdf_path, 'wb') as f:
            await f.write(content)
        
        logger.info(f"Fichier PDF sauvegardé: {pdf_path}")
        
        # Analyse du PDF avec Ollama
        analyzer = PDFAnalyzer()
        product_data = await analyzer.analyze_pdf(pdf_path)
        
        logger.info(f"Données produit extraites: {product_data.get('product_name', 'N/A')}")
        
        # Génération des fichiers de sortie
        results = {}
        
        if output_format in ["html", "both"]:
            html_generator = HTMLGenerator()
            html_path = await html_generator.generate_product_sheet(
                product_data, output_path, session_id
            )
            results["html"] = str(html_path)
        
        if output_format in ["pdf", "both"]:
            pdf_generator = PDFGenerator()
            pdf_path = await pdf_generator.generate_product_pdf(
                product_data, output_path, session_id
            )
            results["pdf"] = str(pdf_path)
        
        return {
            "success": True,
            "session_id": session_id,
            "product_name": product_data.get("product_name", "Produit"),
            "outputs": results,
            "output_directory": str(output_path)
        }
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/{session_id}/{filename}")
async def download_file(session_id: str, filename: str):
    """Téléchargement d'un fichier généré"""
    file_path = Path(settings.OUTPUT_DIR) / session_id / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Fichier non trouvé")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/octet-stream'
    )

@app.get("/health")
async def health_check():
    """Vérification de l'état du service"""
    return {"status": "healthy", "service": "PDF to Product Sheet Generator"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 