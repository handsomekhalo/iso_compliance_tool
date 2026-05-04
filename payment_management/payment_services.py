
# LightningService — abstraction layer over LND + MoneyBadger.
# All LND and MoneyBadger calls go through here — views never talk
# to external services directly.
#
# MOCK MODE (default for sandbox/dev):
#   Set LIGHTNING_MOCK_MODE=True in settings.py
#   Returns realistic fake responses so the full flow works without a node.
#
# LIVE MODE:
#   Set LIGHTNING_MOCK_MODE=False and provide:
#       LND_REST_HOST      e.g. https://your-node.voltageapp.io:8080
#       LND_MACAROON_HEX   admin macaroon hex string
#       MONEYBADGER_API_KEY
#       MONEYBADGER_API_URL e.g. https://api.moneybadger.io/v1

import hashlib
import hmac
import logging
import secrets
import time
from decimal import Decimal

from django.conf import settings

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Config helpers
# ─────────────────────────────────────────────────────────────────────────────

def _mock_mode():
    return getattr(settings, 'LIGHTNING_MOCK_MODE', True)


def _lnd_host():
    return getattr(settings, 'LND_REST_HOST', 'https://localhost:8080')


def _lnd_macaroon():
    return getattr(settings, 'LND_MACAROON_HEX', '')


def _mb_api_key():
    return getattr(settings, 'MONEYBADGER_API_KEY', '')


def _mb_api_url():
    return getattr(settings, 'MONEYBADGER_API_URL', 'https://api.moneybadger.io/v1')


def _webhook_secret():
    return getattr(settings, 'LIGHTNING_WEBHOOK_SECRET', 'change-me-in-production')


# ─────────────────────────────────────────────────────────────────────────────
# Webhook signature verification
# ─────────────────────────────────────────────────────────────────────────────

def verify_webhook_signature(request_body: bytes, signature_header: str) -> bool:
    """
    HMAC-SHA256 verification of incoming webhook.
    Provider signs the body with LIGHTNING_WEBHOOK_SECRET.
    Header expected: X-RandRail-Signature: sha256=<hex>
    """
    if not signature_header:
        return False

    expected = 'sha256=' + hmac.new(
        _webhook_secret().encode(),
        request_body,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, signature_header)


# ─────────────────────────────────────────────────────────────────────────────
# BTC/ZAR exchange rate
# ─────────────────────────────────────────────────────────────────────────────

def get_btc_zar_rate() -> Decimal:
    """
    Fetch live BTC/ZAR rate.
    In mock mode returns a fixed rate.
    In live mode hits a price feed (VALR public ticker — no auth needed).
    """
    if _mock_mode():
        return Decimal('1800000.00')  # R1.8M per BTC — adjust as needed

    try:
        import requests
        response = requests.get(
            'https://api.valr.com/v1/public/BTCZAR/marketsummary',
            timeout=5
        )
        data = response.json()
        return Decimal(str(data['lastTradedPrice']))
    except Exception as exc:
        logger.error(f"[LightningService] Failed to fetch BTC/ZAR rate: {exc}")
        raise ValueError("Could not fetch live BTC/ZAR exchange rate. Try again.")


def zar_to_sats(amount_zar: Decimal, rate: Decimal) -> int:
    """Convert ZAR amount to satoshis given a BTC/ZAR rate."""
    btc_amount = amount_zar / rate
    sats = int(btc_amount * Decimal('100000000'))  # 1 BTC = 100,000,000 sats
    return sats


# ─────────────────────────────────────────────────────────────────────────────
# LND — invoice generation
# ─────────────────────────────────────────────────────────────────────────────

def create_lightning_invoice(amount_sats: int, memo: str = '') -> dict:
    """
    Creates a BOLT11 Lightning invoice via LND REST API.

    Returns:
        {
            'payment_request': 'lnbc...',   # BOLT11 invoice
            'payment_hash':    'abc123...',  # hex string
            'expiry':          3600,         # seconds
        }
    """
    if _mock_mode():
        mock_hash = secrets.token_hex(32)
        return {
            'payment_request': f'lnbc{amount_sats}n1mock{mock_hash[:20]}',
            'payment_hash':    mock_hash,
            'expiry':          3600,
        }

    try:
        import requests
        import base64

        macaroon = _lnd_macaroon()
        headers  = {'Grpc-Metadata-macaroon': macaroon}
        payload  = {'value': amount_sats, 'memo': memo, 'expiry': 3600}

        response = requests.post(
            f"{_lnd_host()}/v1/invoices",
            json=payload,
            headers=headers,
            verify=False,  # self-signed cert on most LND nodes
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        # LND returns payment_hash as base64 — convert to hex
        payment_hash_hex = base64.b64decode(data['r_hash']).hex()

        return {
            'payment_request': data['payment_request'],
            'payment_hash':    payment_hash_hex,
            'expiry':          3600,
        }
    except Exception as exc:
        logger.error(f"[LightningService] LND invoice creation failed: {exc}")
        raise ValueError(f"Failed to create Lightning invoice: {str(exc)}")


# ─────────────────────────────────────────────────────────────────────────────
# MoneyBadger — off-ramp initiation
# ─────────────────────────────────────────────────────────────────────────────

def initiate_offramp(
    payment_hash: str,
    amount_zar: Decimal,
    recipient_account: str,
    provider: str = 'moneybadger'
) -> dict:
    """
    Notifies the off-ramp provider to expect a Lightning payment
    and prepare the ZAR payout.

    Returns:
        {
            'offramp_reference': 'MB-12345',
            'offramp_status':    'pending',
            'raw':               { ...full provider response... }
        }
    """
    if _mock_mode():
        return {
            'offramp_reference': f'MOCK-{provider.upper()}-{secrets.token_hex(6).upper()}',
            'offramp_status':    'pending',
            'raw': {
                'provider':          provider,
                'payment_hash':      payment_hash,
                'amount_zar':        str(amount_zar),
                'recipient_account': recipient_account,
                'mock':              True,
            }
        }

    if provider == 'moneybadger':
        try:
            import requests
            headers = {
                'Authorization': f'Bearer {_mb_api_key()}',
                'Content-Type':  'application/json',
            }
            payload = {
                'payment_hash':      payment_hash,
                'amount_zar':        str(amount_zar),
                'recipient_account': recipient_account,
            }
            response = requests.post(
                f"{_mb_api_url()}/offramp/initiate",
                json=payload,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return {
                'offramp_reference': data.get('reference', ''),
                'offramp_status':    data.get('status', 'pending'),
                'raw':               data,
            }
        except Exception as exc:
            logger.error(f"[LightningService] MoneyBadger off-ramp failed: {exc}")
            raise ValueError(f"Off-ramp initiation failed: {str(exc)}")

    raise ValueError(f"Unsupported off-ramp provider: {provider}")


# ─────────────────────────────────────────────────────────────────────────────
# Main service entry point
# ─────────────────────────────────────────────────────────────────────────────

class LightningService:
    """
    Orchestrates the full payment flow:
        1. Get BTC/ZAR rate
        2. Convert ZAR → sats
        3. Create LND invoice
        4. Notify off-ramp provider
        5. Return all data needed to create LightningPayment record
    """

    @staticmethod
    def initiate_payment(amount_zar: Decimal, recipient_account: str,
                         offramp_provider: str = 'moneybadger',
                         description: str = '') -> dict:
        """
        Full initiation flow. Returns a dict ready to be saved to LightningPayment.
        Raises ValueError on any failure — caller handles the response.
        """
        # 1. Exchange rate
        rate = get_btc_zar_rate()
        amount_sats = zar_to_sats(amount_zar, rate)

        if amount_sats < 1:
            raise ValueError("Amount too small — results in less than 1 satoshi.")

        # 2. LND invoice
        invoice = create_lightning_invoice(
            amount_sats=amount_sats,
            memo=description or f"RandRail payment {amount_zar} ZAR"
        )

        # 3. Off-ramp
        offramp = initiate_offramp(
            payment_hash=invoice['payment_hash'],
            amount_zar=amount_zar,
            recipient_account=recipient_account,
            provider=offramp_provider,
        )

        return {
            'amount_sats':       amount_sats,
            'exchange_rate':     rate,
            'payment_request':   invoice['payment_request'],
            'payment_hash':      invoice['payment_hash'],
            'offramp_provider':  offramp_provider,
            'offramp_reference': offramp['offramp_reference'],
            'offramp_status':    offramp['offramp_status'],
            'raw_response':      offramp['raw'],
        }

    @staticmethod
    def generate_xrpl_hash(payment_hash: str, amount_zar: Decimal) -> str:
        """
        Consistent audit hash for Lightning payments —
        same pattern as reconciliation engine.
        """
        payload = f"{payment_hash}:{amount_zar}:{int(time.time())}"
        return hashlib.sha256(payload.encode()).hexdigest()
