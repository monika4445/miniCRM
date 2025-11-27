from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Lead, Source, Request, Operator
from app.schemas import (
    RequestCreate,
    RequestResponse,
    LeadResponse,
    LeadWithRequestsResponse,
    DistributionStats,
)
from app.services import DistributionService

router = APIRouter(prefix="/requests", tags=["requests"])


@router.post("/", response_model=RequestResponse, status_code=201)
def create_request(request_data: RequestCreate, db: Session = Depends(get_db)):
    """
    Register a new request from a lead.

    Process:
    1. Find or create lead by external_id
    2. Verify source exists
    3. Assign operator using weighted distribution algorithm
    4. Create request record

    If no suitable operators available, request is created without operator assignment.

    Args:
        request_data: Request details including lead external ID, source ID, and message

    Returns:
        Created request with assigned operator (if available)
    """
    lead = db.query(Lead).filter(
        Lead.external_id == request_data.lead_external_id
    ).first()

    if not lead:
        lead = Lead(
            external_id=request_data.lead_external_id,
            name=request_data.lead_name,
            email=request_data.lead_email,
            phone=request_data.lead_phone
        )
        db.add(lead)
        db.flush()

    source = db.query(Source).filter(Source.id == request_data.source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    assigned_operator = DistributionService.assign_operator_to_request(
        db, request_data.source_id
    )

    db_request = Request(
        lead_id=lead.id,
        source_id=request_data.source_id,
        operator_id=assigned_operator.id if assigned_operator else None,
        message=request_data.message,
        status="active"
    )
    db.add(db_request)
    db.commit()
    db.refresh(db_request)

    return RequestResponse(
        id=db_request.id,
        lead_id=db_request.lead_id,
        source_id=db_request.source_id,
        operator_id=db_request.operator_id,
        operator_name=assigned_operator.name if assigned_operator else None,
        status=db_request.status,
        message=db_request.message,
        created_at=db_request.created_at
    )


@router.get("/", response_model=List[RequestResponse])
def list_requests(
    source_id: int = None,
    operator_id: int = None,
    db: Session = Depends(get_db)
):
    """
    Get list of all requests with optional filtering.

    Args:
        source_id: Optional filter by source
        operator_id: Optional filter by operator

    Returns:
        List of requests
    """
    query = db.query(Request)

    if source_id:
        query = query.filter(Request.source_id == source_id)
    if operator_id:
        query = query.filter(Request.operator_id == operator_id)

    requests = query.all()

    return [
        RequestResponse(
            id=req.id,
            lead_id=req.lead_id,
            source_id=req.source_id,
            operator_id=req.operator_id,
            operator_name=req.operator.name if req.operator else None,
            status=req.status,
            message=req.message,
            created_at=req.created_at
        )
        for req in requests
    ]


@router.get("/{request_id}", response_model=RequestResponse)
def get_request(request_id: int, db: Session = Depends(get_db)):
    """
    Get a specific request by ID.

    Args:
        request_id: Request ID

    Returns:
        Request details
    """
    request = db.query(Request).filter(Request.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    return RequestResponse(
        id=request.id,
        lead_id=request.lead_id,
        source_id=request.source_id,
        operator_id=request.operator_id,
        operator_name=request.operator.name if request.operator else None,
        status=request.status,
        message=request.message,
        created_at=request.created_at
    )


@router.patch("/{request_id}/status")
def update_request_status(
    request_id: int,
    status: str,
    db: Session = Depends(get_db)
):
    """
    Update request status (active, closed, etc.).

    This affects operator's current load calculation.

    Args:
        request_id: Request ID
        status: New status

    Returns:
        Updated request
    """
    request = db.query(Request).filter(Request.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    request.status = status
    db.commit()
    db.refresh(request)

    return RequestResponse(
        id=request.id,
        lead_id=request.lead_id,
        source_id=request.source_id,
        operator_id=request.operator_id,
        operator_name=request.operator.name if request.operator else None,
        status=request.status,
        message=request.message,
        created_at=request.created_at
    )


@router.get("/leads/all", response_model=List[LeadWithRequestsResponse])
def list_leads_with_requests(db: Session = Depends(get_db)):
    """
    Get all leads with their requests.

    Shows that one lead can have multiple requests from different sources.

    Returns:
        List of leads with their associated requests
    """
    leads = db.query(Lead).all()

    result = []
    for lead in leads:
        requests = [
            RequestResponse(
                id=req.id,
                lead_id=req.lead_id,
                source_id=req.source_id,
                operator_id=req.operator_id,
                operator_name=req.operator.name if req.operator else None,
                status=req.status,
                message=req.message,
                created_at=req.created_at
            )
            for req in lead.requests
        ]

        result.append(
            LeadWithRequestsResponse(
                lead=LeadResponse(
                    id=lead.id,
                    external_id=lead.external_id,
                    name=lead.name,
                    email=lead.email,
                    phone=lead.phone,
                    created_at=lead.created_at
                ),
                requests=requests
            )
        )

    return result


@router.get("/distribution/stats", response_model=List[DistributionStats])
def get_distribution_statistics(db: Session = Depends(get_db)):
    """
    Get distribution statistics by source.

    Shows how requests are distributed among operators for each source.

    Returns:
        List of statistics per source
    """
    sources = db.query(Source).all()

    result = []
    for source in sources:
        requests = db.query(Request).filter(Request.source_id == source.id).all()

        operator_stats = {}
        for req in requests:
            if req.operator_id:
                if req.operator_id not in operator_stats:
                    operator_stats[req.operator_id] = {
                        "operator_id": req.operator_id,
                        "operator_name": req.operator.name,
                        "request_count": 0
                    }
                operator_stats[req.operator_id]["request_count"] += 1

        result.append(
            DistributionStats(
                source_id=source.id,
                source_name=source.name,
                total_requests=len(requests),
                operators=list(operator_stats.values())
            )
        )

    return result
