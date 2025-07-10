import aiofiles
import logging
from pathlib import Path
from typing import Dict, Any
from weasyprint import HTML, CSS
from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)

class PDFGenerator:
    def __init__(self):
        # Configuration de Jinja2
        template_dir = Path(__file__).parent.parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )
        
    async def generate_product_pdf(
        self, 
        product_data: Dict[str, Any], 
        output_path: Path, 
        session_id: str
    ) -> Path:
        """Génère une fiche produit PDF"""
        try:
            logger.info(f"Génération de la fiche produit PDF pour {product_data.get('product_name', 'Produit')}")
            
            # Rendu du template HTML
            template = self.env.get_template("product_sheet.html")
            html_content = template.render(
                product=product_data,
                session_id=session_id
            )
            
            # Génération du PDF avec WeasyPrint
            html_doc = HTML(string=html_content)
            
            # CSS pour l'impression
            css_content = """
            @page {
                size: A4;
                margin: 2cm;
            }
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
            }
            .header {
                text-align: center;
                margin-bottom: 2em;
                border-bottom: 2px solid #007bff;
                padding-bottom: 1em;
            }
            .product-info {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 2em;
                margin-bottom: 2em;
            }
            .specs-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 1em;
                margin: 1em 0;
            }
            .feature-list {
                list-style: none;
                padding: 0;
            }
            .feature-list li {
                padding: 0.5em 0;
                border-bottom: 1px solid #eee;
            }
            .certification-badge {
                display: inline-block;
                background: #28a745;
                color: white;
                padding: 0.3em 0.8em;
                border-radius: 15px;
                margin: 0.2em;
                font-size: 0.9em;
            }
            """
            
            css_doc = CSS(string=css_content)
            
            # Génération du PDF
            pdf_filename = f"fiche_produit_{session_id}.pdf"
            pdf_path = output_path / pdf_filename
            
            html_doc.write_pdf(pdf_path, stylesheets=[css_doc])
            
            logger.info(f"Fiche produit PDF générée: {pdf_path}")
            return pdf_path
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération PDF: {str(e)}", exc_info=True)
            raise Exception(f"Erreur lors de la génération PDF: {str(e)}") 