from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class FarmBase(BaseModel):
    name: str
    location: Optional[str] = None
    area_hectares: Optional[float] = None
    crop_type: Optional[str] = None


class FarmCreate(FarmBase):
    agronomist_id: int

class FarmResponse(FarmBase):
    id: int
    agronomist_id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True