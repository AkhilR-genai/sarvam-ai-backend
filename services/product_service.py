import uuid
from datetime import datetime
from typing import Dict, Optional
from models.schemas import ProductKnowledgeRequest, ProductKnowledgeResponse


class ProductService:
    def __init__(self):
        self.products: Dict[str, dict] = {}

    def save_product(self, request: ProductKnowledgeRequest) -> ProductKnowledgeResponse:
        """Save product knowledge base"""
        product_id = str(uuid.uuid4())
        now = datetime.now()
        
        product_data = {
            "id": product_id,
            "description": request.description,
            "product_name": request.product_name,
            "features": request.features,
            "pricing": request.pricing,
            "created_at": now,
            "updated_at": now
        }
        
        self.products[product_id] = product_data
        
        return ProductKnowledgeResponse(
            id=product_id,
            description=request.description,
            product_name=request.product_name,
            created_at=now,
            updated_at=now
        )

    def get_product(self, product_id: str) -> Optional[dict]:
        """Get product by ID"""
        return self.products.get(product_id)

    def list_products(self) -> list:
        """List all products"""
        return list(self.products.values())


# Global instance
product_service = ProductService()
