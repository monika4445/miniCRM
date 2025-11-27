from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Source, Operator, OperatorSourceWeight
from app.schemas import (
    SourceCreate,
    SourceResponse,
    OperatorSourceWeightCreate,
    OperatorSourceWeightResponse,
)

router = APIRouter(prefix="/sources", tags=["sources"])


@router.post("/", response_model=SourceResponse, status_code=201)
def create_source(source: SourceCreate, db: Session = Depends(get_db)):
    """
    Create a new source (bot/channel).

    Args:
        source: Source data including name and description

    Returns:
        Created source
    """
    db_source = db.query(Source).filter(Source.name == source.name).first()
    if db_source:
        raise HTTPException(status_code=400, detail="Source with this name already exists")

    db_source = Source(
        name=source.name,
        description=source.description
    )
    db.add(db_source)
    db.commit()
    db.refresh(db_source)

    return db_source


@router.get("/", response_model=List[SourceResponse])
def list_sources(db: Session = Depends(get_db)):
    """
    Get list of all sources.

    Returns:
        List of all sources
    """
    sources = db.query(Source).all()
    return sources


@router.get("/{source_id}", response_model=SourceResponse)
def get_source(source_id: int, db: Session = Depends(get_db)):
    """
    Get a specific source by ID.

    Args:
        source_id: Source ID

    Returns:
        Source details
    """
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    return source


@router.post("/{source_id}/weights", response_model=List[OperatorSourceWeightResponse], status_code=201)
def configure_source_weights(
    source_id: int,
    weights: List[OperatorSourceWeightCreate],
    db: Session = Depends(get_db)
):
    """
    Configure operator weights for a source.
    This replaces existing weight configuration.

    Args:
        source_id: Source ID
        weights: List of operator weights

    Returns:
        List of configured weights
    """
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    db.query(OperatorSourceWeight).filter(
        OperatorSourceWeight.source_id == source_id
    ).delete()

    created_weights = []
    for weight_data in weights:
        operator = db.query(Operator).filter(
            Operator.id == weight_data.operator_id
        ).first()
        if not operator:
            raise HTTPException(
                status_code=404,
                detail=f"Operator with ID {weight_data.operator_id} not found"
            )

        if weight_data.weight <= 0:
            raise HTTPException(
                status_code=400,
                detail="Weight must be a positive integer"
            )

        db_weight = OperatorSourceWeight(
            operator_id=weight_data.operator_id,
            source_id=source_id,
            weight=weight_data.weight
        )
        db.add(db_weight)
        created_weights.append(db_weight)

    db.commit()

    result = []
    for weight in created_weights:
        db.refresh(weight)
        result.append(
            OperatorSourceWeightResponse(
                id=weight.id,
                operator_id=weight.operator_id,
                source_id=weight.source_id,
                weight=weight.weight,
                operator_name=weight.operator.name
            )
        )

    return result


@router.get("/{source_id}/weights", response_model=List[OperatorSourceWeightResponse])
def get_source_weights(source_id: int, db: Session = Depends(get_db)):
    """
    Get weight configuration for a source.

    Args:
        source_id: Source ID

    Returns:
        List of operator weights for this source
    """
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    weights = db.query(OperatorSourceWeight).filter(
        OperatorSourceWeight.source_id == source_id
    ).all()

    return [
        OperatorSourceWeightResponse(
            id=w.id,
            operator_id=w.operator_id,
            source_id=w.source_id,
            weight=w.weight,
            operator_name=w.operator.name
        )
        for w in weights
    ]


@router.delete("/{source_id}", status_code=204)
def delete_source(source_id: int, db: Session = Depends(get_db)):
    """
    Delete a source.

    Args:
        source_id: Source ID
    """
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    db.delete(source)
    db.commit()
    return None
