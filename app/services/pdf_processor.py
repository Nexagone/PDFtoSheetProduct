import fitz
from pathlib import Path
from PIL import Image
import io
from typing import Tuple, List, Dict
from loguru import logger

class PDFProcessor:
    """Service de traitement des fichiers PDF."""

    def __init__(self, max_pages: int = 5):
        """
        Initialise le processeur PDF.
        
        Args:
            max_pages: Nombre maximum de pages à traiter
        """
        self.max_pages = max_pages

    async def process_pdf(self, file_path: str) -> Tuple[List[Image.Image], str]:
        """
        Traite un fichier PDF pour en extraire les images et le texte.
        
        Args:
            file_path: Chemin vers le fichier PDF
            
        Returns:
            Tuple contenant la liste des images et le texte extrait
        """
        try:
            pdf_document = fitz.open(file_path)
            images = []
            full_text = ""

            # Limite le nombre de pages à traiter
            pages_to_process = min(len(pdf_document), self.max_pages)
            
            for page_num in range(pages_to_process):
                page = pdf_document[page_num]
                
                # Extraction du texte
                full_text += page.get_text()
                
                # Conversion de la page en image
                pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                images.append(img)
                
                # Extraction des images intégrées
                image_list = page.get_images()
                for img_index, img_info in enumerate(image_list):
                    try:
                        xref = img_info[0]
                        base_image = pdf_document.extract_image(xref)
                        image_bytes = base_image["image"]
                        
                        # Conversion en objet PIL
                        img = Image.open(io.BytesIO(image_bytes))
                        if img.size[0] > 100 and img.size[1] > 100:  # Filtre les petites images
                            images.append(img)
                    except Exception as e:
                        logger.warning(f"Erreur lors de l'extraction de l'image {img_index}: {str(e)}")

            pdf_document.close()
            return images, full_text

        except Exception as e:
            logger.error(f"Erreur lors du traitement du PDF: {str(e)}")
            raise ValueError(f"Impossible de traiter le PDF: {str(e)}")

    @staticmethod
    def optimize_image(image: Image.Image, max_size: Tuple[int, int] = (800, 800)) -> Image.Image:
        """
        Optimise une image pour l'analyse par l'IA.
        
        Args:
            image: Image à optimiser
            max_size: Taille maximale de l'image
            
        Returns:
            Image optimisée
        """
        try:
            # Redimensionnement si nécessaire
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Conversion en RGB si nécessaire
            if image.mode not in ('RGB', 'L'):
                image = image.convert('RGB')
            
            return image
        except Exception as e:
            logger.error(f"Erreur lors de l'optimisation de l'image: {str(e)}")
            raise ValueError(f"Impossible d'optimiser l'image: {str(e)}")

    def get_metadata(self, file_path: str) -> Dict[str, str]:
        """
        Extrait les métadonnées du PDF.
        
        Args:
            file_path: Chemin vers le fichier PDF
            
        Returns:
            Dictionnaire des métadonnées
        """
        try:
            doc = fitz.open(file_path)
            metadata = {
                "title": doc.metadata.get("title", ""),
                "author": doc.metadata.get("author", ""),
                "subject": doc.metadata.get("subject", ""),
                "keywords": doc.metadata.get("keywords", ""),
                "creator": doc.metadata.get("creator", ""),
                "producer": doc.metadata.get("producer", ""),
                "page_count": len(doc)
            }
            doc.close()
            return metadata
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des métadonnées: {str(e)}")
            return {} 