from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class OperatorCreate(BaseModel):
    name: str
    is_active: bool = True
    max_load: int


class OperatorUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    max_load: Optional[int] = None


class OperatorResponse(BaseModel):
    id: int
    name: str
    is_active: bool
    max_load: int
    current_load: int
    created_at: datetime

    class Config:
        from_attributes = True


class LeadResponse(BaseModel):
    id: int
    external_id: str
    name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class SourceCreate(BaseModel):
    name: str
    description: Optional[str] = None


class SourceResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class OperatorSourceWeightCreate(BaseModel):
    operator_id: int
    weight: int


class OperatorSourceWeightResponse(BaseModel):
    id: int
    operator_id: int
    source_id: int
    weight: int
    operator_name: str

    class Config:
        from_attributes = True


class RequestCreate(BaseModel):
    lead_external_id: str
    source_id: int
    message: Optional[str] = None
    lead_name: Optional[str] = None
    lead_email: Optional[str] = None
    lead_phone: Optional[str] = None


class RequestResponse(BaseModel):
    id: int
    lead_id: int
    source_id: int
    operator_id: Optional[int]
    operator_name: Optional[str]
    status: str
    message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class LeadWithRequestsResponse(BaseModel):
    lead: LeadResponse
    requests: List[RequestResponse]


class DistributionStats(BaseModel):
    source_id: int
    source_name: str
    total_requests: int
    operators: List[dict]
