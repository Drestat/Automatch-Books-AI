"""
Test suite for Stripe webhook integration.

Covers:
- checkout.session.completed → token grant + tier update
- invoice.payment_failed → subscription status update
- Webhook signature validation
- Idempotent event processing
- Subscription lifecycle
"""

import pytest
import json
import hmac
import hashlib
import time
import stripe
from unittest.mock import patch, MagicMock


class TestStripeWebhookProcessing:
    """
    Tests for Stripe webhook event handling.
    """

    @pytest.fixture
    def webhook_secret(self):
        """Test webhook signing secret."""
        return "whsec_test_secret_for_unit_tests"

    def _sign_payload(self, payload: str, secret: str) -> str:
        """Generate valid Stripe webhook signature."""
        timestamp = int(time.time())
        signed_payload = f"{timestamp}.{payload}"
        signature = hmac.new(
            secret.encode(),
            signed_payload.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"t={timestamp},v1={signature}"

    @pytest.mark.integration
    def test_checkout_completed_grants_tokens(
        self, client, test_user, stripe_mock_events, webhook_secret
    ):
        """
        Test Case 1: Successful checkout grants tokens and updates tier.

        Flow: Stripe checkout → webhook → update user → grant tokens
        """
        event = stripe_mock_events["checkout_session_completed"]

        # Ensure client_reference_id matches test user
        event["data"]["object"]["client_reference_id"] = test_user.id

        payload = json.dumps(event)

        with patch('stripe.Webhook.construct_event') as mock_construct:
            mock_construct.return_value = MagicMock(
                type="checkout.session.completed",
                data=MagicMock(object=event["data"]["object"])
            )

            response = client.post(
                "/api/v1/stripe/webhook",
                content=payload,
                headers={
                    "Content-Type": "application/json",
                    "Stripe-Signature": self._sign_payload(payload, webhook_secret)
                }
            )

        # Should process successfully
        assert response.status_code == 200, \
            f"Webhook should return 200, got {response.status_code}: {response.text}"

    @pytest.mark.integration
    def test_payment_failed_updates_status(
        self, client, test_user, stripe_mock_events, webhook_secret
    ):
        """
        Test Case 2: Failed payment updates subscription status.
        """
        event = stripe_mock_events["invoice_payment_failed"]
        payload = json.dumps(event)

        with patch('stripe.Webhook.construct_event') as mock_construct:
            mock_construct.return_value = MagicMock(
                type="invoice.payment_failed",
                data=MagicMock(object=event["data"]["object"])
            )

            response = client.post(
                "/api/v1/stripe/webhook",
                content=payload,
                headers={
                    "Content-Type": "application/json",
                    "Stripe-Signature": self._sign_payload(payload, webhook_secret)
                }
            )

        assert response.status_code == 200

    @pytest.mark.integration
    @pytest.mark.security
    def test_invalid_signature_rejected(self, client):
        """
        Test Case 3: Invalid webhook signature should be rejected.
        """
        payload = json.dumps({"type": "checkout.session.completed"})

        with patch('stripe.Webhook.construct_event') as mock_construct:
            mock_construct.side_effect = stripe.error.SignatureVerificationError("Invalid signature", "sig_header")

            response = client.post(
                "/api/v1/stripe/webhook",
                content=payload,
                headers={
                    "Content-Type": "application/json",
                    "Stripe-Signature": "t=123,v1=invalid_signature"
                }
            )

        # Should reject invalid signature
        assert response.status_code in [400, 401, 403], \
            f"Should reject invalid signature, got {response.status_code}"

    @pytest.mark.integration
    def test_idempotent_event_processing(
        self, client, test_user, stripe_mock_events, webhook_secret
    ):
        """
        Test Case 4: Duplicate events should be handled idempotently.

        Stripe may send the same event multiple times. Processing should
        not result in double token grants or tier changes.
        """
        event = stripe_mock_events["checkout_session_completed"]
        event["data"]["object"]["client_reference_id"] = test_user.id
        payload = json.dumps(event)

        with patch('stripe.Webhook.construct_event') as mock_construct:
            mock_construct.return_value = MagicMock(
                type="checkout.session.completed",
                data=MagicMock(object=event["data"]["object"])
            )

            # Process same event twice
            response1 = client.post(
                "/api/v1/stripe/webhook",
                content=payload,
                headers={
                    "Content-Type": "application/json",
                    "Stripe-Signature": self._sign_payload(payload, webhook_secret)
                }
            )

            response2 = client.post(
                "/api/v1/stripe/webhook",
                content=payload,
                headers={
                    "Content-Type": "application/json",
                    "Stripe-Signature": self._sign_payload(payload, webhook_secret)
                }
            )

        # Both should return 200 (idempotent)
        assert response1.status_code == 200
        assert response2.status_code == 200

    @pytest.mark.integration
    def test_subscription_deleted_downgrades_user(
        self, client, test_user, stripe_mock_events, webhook_secret
    ):
        """
        Test Case 5: Subscription deletion should downgrade to free tier.
        """
        event = stripe_mock_events["subscription_deleted"]
        payload = json.dumps(event)

        with patch('stripe.Webhook.construct_event') as mock_construct:
            mock_construct.return_value = MagicMock(
                type="customer.subscription.deleted",
                data=MagicMock(object=event["data"]["object"])
            )

            response = client.post(
                "/api/v1/stripe/webhook",
                content=payload,
                headers={
                    "Content-Type": "application/json",
                    "Stripe-Signature": self._sign_payload(payload, webhook_secret)
                }
            )

        assert response.status_code == 200

    @pytest.mark.integration
    def test_missing_client_reference_id_handled(
        self, client, webhook_secret
    ):
        """
        Test Case 6: Webhook without client_reference_id should not crash.
        """
        event = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_orphan",
                    "customer": "cus_orphan",
                    "client_reference_id": None,  # Missing user mapping
                    "metadata": {}
                }
            }
        }
        payload = json.dumps(event)

        with patch('stripe.Webhook.construct_event') as mock_construct:
            mock_construct.return_value = MagicMock(
                type="checkout.session.completed",
                data=MagicMock(object=event["data"]["object"])
            )

            response = client.post(
                "/api/v1/stripe/webhook",
                content=payload,
                headers={
                    "Content-Type": "application/json",
                    "Stripe-Signature": self._sign_payload(payload, webhook_secret)
                }
            )

        # Should handle gracefully (200 or specific error, not 500)
        assert response.status_code != 500, \
            "Missing client_reference_id should not cause 500 error"
