from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

class Dimensions(BaseModel):
    """Modèle pour les dimensions du produit."""
    longueur: str = Field(..., description="Longueur du produit")
    largeur: str = Field(..., description="Largeur du produit")
    hauteur: str = Field(..., description="Hauteur du produit")

class ProductSheet(BaseModel):
    """Modèle principal pour une fiche produit."""
    product_name: str = Field(..., description="Nom du produit")
    brand: str = Field(..., description="Marque du produit")
    model_number: str = Field(..., description="Numéro de modèle")
    category: str = Field(..., description="Catégorie du produit")
    technical_specs: Dict[str, Any] = Field(
        ...,
        description="Spécifications techniques sous forme de dictionnaire"
    )
    dimensions: Dimensions = Field(..., description="Dimensions du produit")
    weight: str = Field(..., description="Poids du produit")
    power_consumption: str = Field(..., description="Consommation électrique")
    features: List[str] = Field(..., description="Liste des fonctionnalités")
    warranty: str = Field(..., description="Informations sur la garantie")
    price_range: Optional[str] = Field(
        None,
        description="Fourchette de prix indicative (optionnel)"
    )
    description: str = Field(..., description="Description détaillée du produit")

    class Config:
        json_schema_extra = {
            "example": {
                "product_name": "Réfrigérateur XC500",
                "brand": "CoolTech",
                "model_number": "CT-RF500",
                "category": "Électroménager",
                "technical_specs": {
                    "volume": "500L",
                    "classe_energetique": "A++",
                    "temperature_min": "2°C",
                    "temperature_max": "8°C"
                },
                "dimensions": {
                    "longueur": "70cm",
                    "largeur": "80cm",
                    "hauteur": "180cm"
                },
                "weight": "75kg",
                "power_consumption": "250kWh/an",
                "features": [
                    "No Frost",
                    "Distributeur d'eau",
                    "Compartiment 0°C"
                ],
                "warranty": "2 ans pièces et main d'œuvre",
                "price_range": "800€ - 1000€",
                "description": "Réfrigérateur haut de gamme avec technologie No Frost..."
            }
        } 