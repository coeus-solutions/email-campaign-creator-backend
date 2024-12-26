from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from config.supabase import supabase
from .auth import get_current_user

router = APIRouter()

class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ProductResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    created_by: str

@router.post("/", response_model=ProductResponse)
async def create_product(product: ProductCreate, current_user: str = Depends(get_current_user)):
    try:
        now = datetime.utcnow().isoformat()
        result = supabase.table('products').insert({
            "name": product.name,
            "description": product.description,
            "created_by": current_user,
            "created_at": now,
            "updated_at": now
        }).execute()
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(product_id: str, product: ProductCreate, current_user: str = Depends(get_current_user)):
    try:
        # Check if product exists and belongs to the current user
        existing = supabase.table('products').select("*").eq('id', product_id).eq('created_by', current_user).execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Product not found or you don't have permission to update it")
        
        # Update product
        result = supabase.table('products').update({
            "name": product.name,
            "description": product.description,
            "updated_at": datetime.utcnow().isoformat()
        }).eq('id', product_id).execute()
        
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{product_id}")
async def delete_product(product_id: str, current_user: str = Depends(get_current_user)):
    try:
        # Check if product exists and belongs to the current user
        existing = supabase.table('products').select("*").eq('id', product_id).eq('created_by', current_user).execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Product not found or you don't have permission to delete it")
        
        # Delete product
        supabase.table('products').delete().eq('id', product_id).execute()
        return {"message": "Product deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str):
    try:
        result = supabase.table('products').select("*").eq('id', product_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Product not found")
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[ProductResponse])
async def list_products():
    try:
        result = supabase.table('products').select("*").execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 