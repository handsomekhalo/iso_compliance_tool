"""
Core flow: send -> webhook settlement (payment_management app).

Runs entirely in LIGHTNING_MOCK_MODE (set in test_settings.py) so no
real LND/MoneyBadger/VALR calls happen — LightningService returns
deterministic mock data, matching how the app behaves in sandbox.
"""
import json
import pytest
from decimal import Decimal
from django.urls import reverse
from rest_framework.authtoken.models import Token

from payment_management.models import LightningPayment
from payment_management.payment_services import LightningService


def _auth(client, user):
    token, _ = Token.objects.get_or_create(user=user)
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client


@pytest.mark.django_db
class TestSendPayment:

    def test_institution_admin_can_initiate_payment(self, authed_client):
        client, user, bank = authed_client
        payload = {
            "amount_zar": "500.00",
            "recipient_account": "+27821234567",
            "offramp_provider": "moneybadger",
            "description": "test remittance",
        }
        resp = client.post(reverse("send_payment_api"), payload, format="json")

        assert resp.status_code == 201, resp.data
        data = resp.data["data"]
        assert data["status"] == "sent"
        assert data["amount_sats"] > 0
        assert data["xrpl_hash"]  # audit hash present

        payment = LightningPayment.objects.get(bank=bank)
        assert payment.payment_hash
        assert payment.exchange_rate == Decimal("1800000.00")  # fixed mock rate

    def test_analyst_cannot_initiate_payment(self, api_client, analyst_user):
        """send_payment_api requires IsInstitutionAdmin — analysts can view, not send."""
        user, bank = analyst_user
        _auth(api_client, user)
        payload = {"amount_zar": "500.00", "recipient_account": "+27821234567"}
        resp = api_client.post(reverse("send_payment_api"), payload, format="json")
        assert resp.status_code == 403

    def test_rejects_amount_over_sandbox_limit(self, authed_client):
        client, user, bank = authed_client
        payload = {"amount_zar": "50001.00", "recipient_account": "+27821234567"}
        resp = client.post(reverse("send_payment_api"), payload, format="json")
        assert resp.status_code == 400
        assert "sandbox limit" in str(resp.data).lower()

    def test_rejects_blank_recipient(self, authed_client):
        client, user, bank = authed_client
        payload = {"amount_zar": "10.00", "recipient_account": "   "}
        resp = client.post(reverse("send_payment_api"), payload, format="json")
        assert resp.status_code == 400

    def test_requires_authentication(self, api_client):
        payload = {"amount_zar": "10.00", "recipient_account": "+27821234567"}
        resp = api_client.post(reverse("send_payment_api"), payload, format="json")
        assert resp.status_code == 401


@pytest.mark.django_db
class TestPaymentWebhook:

    def _create_sent_payment(self, bank, user):
        result = LightningService.initiate_payment(
            amount_zar=Decimal("100.00"),
            recipient_account="+27821234567",
        )
        xrpl_hash = LightningService.generate_xrpl_hash(result["payment_hash"], Decimal("100.00"))
        return LightningPayment.objects.create(
            bank=bank,
            initiated_by=user,
            amount_zar=Decimal("100.00"),
            amount_sats=result["amount_sats"],
            exchange_rate=result["exchange_rate"],
            status=LightningPayment.Status.SENT,
            payment_request=result["payment_request"],
            payment_hash=result["payment_hash"],
            offramp_provider=result["offramp_provider"],
            offramp_reference=result["offramp_reference"],
            recipient_account="+27821234567",
            xrpl_hash=xrpl_hash,
        )

    def test_webhook_settles_pending_payment(self, api_client, institution_admin):
        user, bank = institution_admin
        payment = self._create_sent_payment(bank, user)

        webhook_payload = {
            "payment_hash": payment.payment_hash,
            "payment_preimage": "deadbeef" * 8,
            "status": "settled",
            "offramp_reference": "MB-99999",
        }
        resp = api_client.post(
            reverse("payment_webhook_api"), data=json.dumps(webhook_payload),
            content_type="application/json",
        )

        assert resp.status_code == 200, resp.data
        payment.refresh_from_db()
        assert payment.status == LightningPayment.Status.SETTLED
        assert payment.payment_preimage == "deadbeef" * 8
        assert payment.settled_at is not None

    def test_webhook_is_idempotent_on_replay(self, api_client, institution_admin):
        """A retried webhook for an already-settled payment must not error or re-mutate state."""
        user, bank = institution_admin
        payment = self._create_sent_payment(bank, user)
        payment.mark_settled(preimage="original-preimage")

        webhook_payload = {
            "payment_hash": payment.payment_hash,
            "payment_preimage": "different-preimage-should-be-ignored",
            "status": "settled",
        }
        resp = api_client.post(
            reverse("payment_webhook_api"), data=json.dumps(webhook_payload),
            content_type="application/json",
        )

        assert resp.status_code == 200
        assert "already processed" in str(resp.data).lower()
        payment.refresh_from_db()
        assert payment.payment_preimage == "original-preimage"  # unchanged

    def test_webhook_marks_failed_payment(self, api_client, institution_admin):
        user, bank = institution_admin
        payment = self._create_sent_payment(bank, user)

        webhook_payload = {
            "payment_hash": payment.payment_hash,
            "status": "failed",
            "failure_reason": "invoice expired before payment",
        }
        resp = api_client.post(
            reverse("payment_webhook_api"), data=json.dumps(webhook_payload),
            content_type="application/json",
        )
        assert resp.status_code == 200
        payment.refresh_from_db()
        assert payment.status == LightningPayment.Status.FAILED
        assert payment.failure_reason == "invoice expired before payment"

    def test_webhook_unknown_payment_hash_returns_404(self, api_client):
        webhook_payload = {"payment_hash": "no-such-hash", "status": "settled"}
        resp = api_client.post(
            reverse("payment_webhook_api"), data=json.dumps(webhook_payload),
            content_type="application/json",
        )
        assert resp.status_code == 404


@pytest.mark.django_db
class TestListAndDetailScoping:

    def test_bank_cannot_see_other_banks_payments(self, authed_client, other_bank_admin):
        client, user, bank = authed_client
        other_user, other_bank = other_bank_admin

        LightningPayment.objects.create(
            bank=other_bank, initiated_by=other_user,
            amount_zar=Decimal("50.00"), status=LightningPayment.Status.SETTLED,
            payment_hash="other-banks-payment",
        )

        resp = client.get(reverse("list_payments_api"))
        assert resp.status_code == 200
        assert resp.data["count"] == 0