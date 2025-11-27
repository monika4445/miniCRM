from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Operator
from app.schemas import OperatorCreate, OperatorUpdate, OperatorResponse

router = APIRouter(prefix="/operators", tags=["operators"])


@router.post("/", response_model=OperatorResponse, status_code=201)
def create_operator(operator: OperatorCreate, db: Session = Depends(get_db)):
    """
    Create a new operator.

    Args:
        operator: Operator data including name, active status, and max load
        db: Database session

    Returns:
        Created operator with current load
    """
    db_operator = Operator(
        name=operator.name,
        is_active=operator.is_active,
        max_load=operator.max_load
    )
    db.add(db_operator)
    db.commit()
    db.refresh(db_operator)

    return OperatorResponse(
        id=db_operator.id,
        name=db_operator.name,
        is_active=db_operator.is_active,
        max_load=db_operator.max_load,
        current_load=db_operator.get_current_load(db),
        created_at=db_operator.created_at
    )


@router.get("/", response_model=List[OperatorResponse])
def list_operators(db: Session = Depends(get_db)):
    """
    Get list of all operators with their current load.

    Returns:
        List of all operators
    """
    operators = db.query(Operator).all()
    return [
        OperatorResponse(
            id=op.id,
            name=op.name,
            is_active=op.is_active,
            max_load=op.max_load,
            current_load=op.get_current_load(db),
            created_at=op.created_at
        )
        for op in operators
    ]


@router.get("/{operator_id}", response_model=OperatorResponse)
def get_operator(operator_id: int, db: Session = Depends(get_db)):
    """
    Get a specific operator by ID.

    Args:
        operator_id: Operator ID

    Returns:
        Operator details with current load
    """
    operator = db.query(Operator).filter(Operator.id == operator_id).first()
    if not operator:
        raise HTTPException(status_code=404, detail="Operator not found")

    return OperatorResponse(
        id=operator.id,
        name=operator.name,
        is_active=operator.is_active,
        max_load=operator.max_load,
        current_load=operator.get_current_load(db),
        created_at=operator.created_at
    )


@router.patch("/{operator_id}", response_model=OperatorResponse)
def update_operator(
    operator_id: int,
    operator_update: OperatorUpdate,
    db: Session = Depends(get_db)
):
    """
    Update operator's properties (name, active status, or max load).

    Args:
        operator_id: Operator ID
        operator_update: Fields to update

    Returns:
        Updated operator
    """
    operator = db.query(Operator).filter(Operator.id == operator_id).first()
    if not operator:
        raise HTTPException(status_code=404, detail="Operator not found")

    if operator_update.name is not None:
        operator.name = operator_update.name
    if operator_update.is_active is not None:
        operator.is_active = operator_update.is_active
    if operator_update.max_load is not None:
        operator.max_load = operator_update.max_load

    db.commit()
    db.refresh(operator)

    return OperatorResponse(
        id=operator.id,
        name=operator.name,
        is_active=operator.is_active,
        max_load=operator.max_load,
        current_load=operator.get_current_load(db),
        created_at=operator.created_at
    )


@router.delete("/{operator_id}", status_code=204)
def delete_operator(operator_id: int, db: Session = Depends(get_db)):
    """
    Delete an operator.

    Args:
        operator_id: Operator ID
    """
    operator = db.query(Operator).filter(Operator.id == operator_id).first()
    if not operator:
        raise HTTPException(status_code=404, detail="Operator not found")

    db.delete(operator)
    db.commit()
    return None
