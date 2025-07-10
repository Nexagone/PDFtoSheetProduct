import aiofiles
import logging
from pathlib import Path
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)

class HTMLGenerator:
    def __init__(self):
        # Configuration de Jinja2
        template_dir = Path(__file__).parent.parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )
        
    async def generate_product_sheet(
        self, 
        product_data: Dict[str, Any], 
        output_path: Path, 
        session_id: str
    ) -> Path:
        """Génère une fiche produit HTML"""
        try:
            logger.info(f"Génération de la fiche produit HTML pour {product_data.get('product_name', 'Produit')}")
            
            # Rendu du template
            template = self.env.get_template("product_sheet.html")
            html_content = template.render(
                product=product_data,
                session_id=session_id
            )
            
            # Sauvegarde du fichier HTML
            html_filename = f"fiche_produit_{session_id}.html"
            html_path = output_path / html_filename
            
            async with aiofiles.open(html_path, 'w', encoding='utf-8') as f:
                await f.write(html_content)
            
            logger.info(f"Fiche produit HTML générée: {html_path}")
            return html_path
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération HTML: {str(e)}", exc_info=True)
            raise Exception(f"Erreur lors de la génération HTML: {str(e)}") 