from pydantic import BaseModel, EmailStr
from models.models import User, UserRole


class TotalProductsResponse(BaseModel):
    total_products: int

class TotalWarehousesResponse(BaseModel):
    total_warehouses: int

class TotalTransactionsResponse(BaseModel):
    total_transactions: int

class AllTransactionsResponse(BaseModel):
    transactions: list[dict]  

class StockByProductResponse(BaseModel):
    stock_by_product: list[dict]

class LowStockProductsResponse(BaseModel):
    low_stock_products: list[dict]