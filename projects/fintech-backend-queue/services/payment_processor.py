"""
Fintech Backend: Payment Processing, Anti-Fraud & Fee Engine
"""

from typing import Dict, Any, Tuple


class PaymentEngine:
    """Core payment processing and validation logic."""

    FEE_PERCENTAGE = 0.025  # 2.5%
    MAX_TRANSACTION_LIMIT = 50000.00

    @staticmethod
    def validate_transaction(tx: Dict[str, Any]) -> Tuple[bool, str]:
        amount = tx.get("amount", 0.0)
        currency = tx.get("currency", "BRL")
        sender = tx.get("sender_account_id")
        recipient = tx.get("recipient_account_id")

        if amount <= 0:
            return False, "Amount must be strictly positive"

        if amount > PaymentEngine.MAX_TRANSACTION_LIMIT:
            return False, f"Transaction exceeds maximum limit of {PaymentEngine.MAX_TRANSACTION_LIMIT}"

        if not sender or not recipient:
            return False, "Sender and recipient accounts are required"

        if sender == recipient:
            return False, "Sender and recipient cannot be the same account"

        if currency not in ("BRL", "USD", "EUR"):
            return False, f"Unsupported currency: {currency}"

        return True, "Valid"

    @staticmethod
    def calculate_fees(amount: float) -> float:
        return round(amount * PaymentEngine.FEE_PERCENTAGE, 2)

    @staticmethod
    def evaluate_fraud_risk(tx: Dict[str, Any]) -> str:
        amount = tx.get("amount", 0.0)
        is_international = tx.get("currency") != "BRL"
        is_first_tx = tx.get("is_first_transaction", False)

        risk_score = 0
        if amount > 10000.0:
            risk_score += 40
        if is_international:
            risk_score += 30
        if is_first_tx:
            risk_score += 30

        if risk_score >= 70:
            return "FLAGGED_FOR_REVIEW"
        elif risk_score >= 40:
            return "MODERATE_RISK"
        return "LOW_RISK"
