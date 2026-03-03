from fastapi import APIRouter, HTTPException
from models.schemas import ProductKnowledgeRequest, ProductKnowledgeResponse
from services.product_service import product_service

router = APIRouter(prefix="/api/product", tags=["product"])


@router.post("/save", response_model=ProductKnowledgeResponse)
async def save_product(request: ProductKnowledgeRequest):
    """
    Save product knowledge base for AI agent
    """
    try:
        product = product_service.save_product(request)
        return product
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{product_id}")
async def get_product(product_id: str):
    """
    Get product details by ID
    """
    product = product_service.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return product


@router.get("/")
async def list_products():
    """
    List all saved products
    """
    products = product_service.list_products()
    return {"products": products, "count": len(products)}
