import random
from typing import Optional
from sqlalchemy.orm import Session
from app.models import Operator, OperatorSourceWeight, Request


class DistributionService:
    """
    Service for distributing requests among operators based on weights and load limits.

    Algorithm:
    1. Find all operators configured for the given source
    2. Filter out inactive operators and operators at max capacity
    3. Select an operator using weighted random selection
    4. If selected operator is at capacity, try to select another available operator
    """

    @staticmethod
    def get_available_operators(db: Session, source_id: int) -> list[tuple[Operator, int]]:
        """
        Get all available operators for a source with their weights.

        Returns:
            List of tuples (operator, weight) for operators that are:
            - Active
            - Have capacity (current load < max load)
            - Configured for this source
        """
        weights = db.query(OperatorSourceWeight).filter(
            OperatorSourceWeight.source_id == source_id
        ).all()

        available_operators = []

        for weight_config in weights:
            operator = weight_config.operator

            if not operator.is_active:
                continue

            current_load = operator.get_current_load(db)
            if current_load >= operator.max_load:
                continue

            available_operators.append((operator, weight_config.weight))

        return available_operators

    @staticmethod
    def select_operator_weighted(
        available_operators: list[tuple[Operator, int]]
    ) -> Optional[Operator]:
        """
        Select an operator using weighted random selection.

        Algorithm:
        - Each operator has a probability proportional to their weight
        - Probability = weight / sum_of_all_weights

        Args:
            available_operators: List of (operator, weight) tuples

        Returns:
            Selected operator or None if no operators available
        """
        if not available_operators:
            return None

        operators = [op for op, _ in available_operators]
        weights = [w for _, w in available_operators]

        selected = random.choices(operators, weights=weights, k=1)[0]
        return selected

    @staticmethod
    def assign_operator_to_request(
        db: Session, source_id: int
    ) -> Optional[Operator]:
        """
        Main method to assign an operator to a new request.

        Process:
        1. Get all available operators for the source
        2. Use weighted random selection to choose one
        3. Return the selected operator or None if no operators available

        Args:
            db: Database session
            source_id: ID of the source (bot) for this request

        Returns:
            Assigned operator or None if no suitable operators found
        """
        available_operators = DistributionService.get_available_operators(
            db, source_id
        )

        if not available_operators:
            return None

        return DistributionService.select_operator_weighted(available_operators)

    @staticmethod
    def get_operator_statistics(db: Session, operator_id: int, source_id: int) -> dict:
        """
        Get distribution statistics for an operator on a specific source.

        Returns:
            Dictionary with total requests and current load
        """
        total_requests = db.query(Request).filter(
            Request.operator_id == operator_id,
            Request.source_id == source_id
        ).count()

        operator = db.query(Operator).filter(Operator.id == operator_id).first()
        current_load = operator.get_current_load(db) if operator else 0

        return {
            "operator_id": operator_id,
            "operator_name": operator.name if operator else "Unknown",
            "total_requests": total_requests,
            "current_load": current_load,
            "max_load": operator.max_load if operator else 0
        }
