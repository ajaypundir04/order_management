from typing import Optional
from pydantic import BaseModel, Field

class OrderResponse(BaseModel):
    id: str = Field(..., alias="id")
    created_at: str
    type_: str = Field(..., alias="type")
    side: str
    instrument: str
    limit_price: Optional[float]
    quantity: int