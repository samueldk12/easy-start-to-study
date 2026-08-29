"""
Unit Tests: Fintech Payment Engine & Anti-Fraud Rules
"""

import pytest
from services.payment_processor import PaymentEngine


@pytest.mark.unit
class TestPaymentProcessor:
    def test_valid_transaction(self):
        tx = {
            "amount": 250.00,
            "currency": "BRL",
            "sender_account_id": "ACC_001",
            "recipient_account_id": "ACC_002"
        }
        valid, msg = PaymentEngine.validate_transaction(tx)
        assert valid is True
        assert msg == "Valid"

    def test_negative_amount_invalid(self):
        tx = {"amount": -50.0, "currency": "BRL", "sender_account_id": "A", "recipient_account_id": "B"}
        valid, msg = PaymentEngine.validate_transaction(tx)
        assert valid is False
        assert "positive" in msg

    def test_same_sender_recipient_invalid(self):
        tx = {"amount": 100.0, "currency": "BRL", "sender_account_id": "ACC_001", "recipient_account_id": "ACC_001"}
        valid, msg = PaymentEngine.validate_transaction(tx)
        assert valid is False

    def test_fee_calculation(self):
        fee = PaymentEngine.calculate_fees(1000.00)
        assert fee == 25.00

    def test_fraud_risk_scoring(self):
        tx_low = {"amount": 150.0, "currency": "BRL"}
        assert PaymentEngine.evaluate_fraud_risk(tx_low) == "LOW_RISK"

        tx_high = {"amount": 15000.0, "currency": "USD", "is_first_transaction": True}
        assert PaymentEngine.evaluate_fraud_risk(tx_high) == "FLAGGED_FOR_REVIEW"
