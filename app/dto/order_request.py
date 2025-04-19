from typing import Optional
from pydantic import BaseModel, Field, condecimal, conint, constr, root_validator
from app.dto.types import OrderType, OrderSide

class OrderRequest(BaseModel):
    type_: OrderType = Field(..., alias="type")
    side: OrderSide
    instrument: constr(min_length=12, max_length=12)  # type: ignore
    limit_price: Optional[condecimal(decimal_places=2)]  # type: ignore
    quantity: conint(gt=0) # type: ignore

    @root_validator
    def validator(cls, values: dict):
        if values.get("type_") == OrderType.MARKET and values.get("limit_price"):
            raise ValueError("Providing a `limit_price` is prohibited for type `market`")
        if values.get("type_") == OrderType.LIMIT and not values.get("limit_price"):
            raise ValueError("Attribute `limit_price` is required for type `limit`")
        return values