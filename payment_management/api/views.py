import logging

from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from compliance_management.models import Bank
from compliance_management.decorators import IsAnalystOrAbove, IsInstitutionAdmin
from payment_management.api.serializers import InitiatePaymentSerializer, LightningPaymenDetailstSerializer, LightningPaymentListSerializer, LightningPaymentSerializer, WebhookPayloadSerializer
from payment_management.models import LightningPayment
from payment_management.payment_services import LightningService, verify_webhook_signature

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Initiate payment
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsInstitutionAdmin])
def send_payment_api(request):
    """
    POST /api/lightning/send/
    Initiate a Lightning payment from the bank's account.
    Institution Admin only.
    """
    serializer = InitiatePaymentSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'message': 'Invalid payment details.',
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        bank = Bank.objects.get(user=request.user)
    except Bank.DoesNotExist:
        return Response(
            {'message': 'Bank not found for authenticated user.'},
            status=status.HTTP_404_NOT_FOUND
        )

    data = serializer.validated_data

    try:
        # Delegate everything to the service layer
        result = LightningService.initiate_payment(
            amount_zar=data['amount_zar'],
            recipient_account=data['recipient_account'],
            offramp_provider=data.get('offramp_provider', 'moneybadger'),
            description=data.get('description', ''),
        )
    except ValueError as exc:
        return Response(
            {'message': str(exc)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as exc:
        logger.error(f"[send_payment_api] Unexpected error: {exc}")
        return Response(
            {'message': 'Payment initiation failed. Please try again.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # Generate audit hash
    xrpl_hash = LightningService.generate_xrpl_hash(
        result['payment_hash'],
        data['amount_zar']
    )

    # Create the payment record
    payment = LightningPayment.objects.create(
        bank=bank,
        initiated_by=request.user,
        amount_zar=data['amount_zar'],
        amount_sats=result['amount_sats'],
        exchange_rate=result['exchange_rate'],
        direction=data.get('direction', 'outbound'),
        status=LightningPayment.Status.SENT,
        payment_request=result['payment_request'],
        payment_hash=result['payment_hash'],
        offramp_provider=result['offramp_provider'],
        offramp_reference=result['offramp_reference'],
        offramp_status=result['offramp_status'],
        recipient_account=data['recipient_account'],
        xrpl_hash=xrpl_hash,
        raw_response=result['raw_response'],
    )

    return Response({
        'message': 'Payment initiated successfully.',
        'data': LightningPaymentSerializer(payment).data,
    }, status=status.HTTP_201_CREATED)


# ─────────────────────────────────────────────────────────────────────────────
# 2. Webhook — settlement callback from LND / MoneyBadger
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([])  # No token auth — uses HMAC signature instead
def payment_webhook_api(request):
    """
    POST /api/lightning/webhook/
    Called by LND or MoneyBadger when a payment settles or fails.
    Secured via HMAC-SHA256 signature on the request body.
    """
    # ── Verify webhook signature ───────────────────────────────────────────
    signature = request.headers.get('X-RandRail-Signature', '')
    # REMOVE BEFORE PRODUCTION
    if getattr(settings, 'LIGHTNING_MOCK_MODE', True):
        pass  # skip signature check in mock mode
    else:
        if not verify_webhook_signature(request.body, signature):
            return Response({'message': 'Invalid signature.'}, status=401)

    
    # if not verify_webhook_signature(request.body, signature):
    #     logger.warning("[payment_webhook_api] Invalid webhook signature rejected.")
    #     return Response(
    #         {'message': 'Invalid signature.'},
    #         status=status.HTTP_401_UNAUTHORIZED
    #     )

    serializer = WebhookPayloadSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'message': 'Invalid webhook payload.',
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)

    payload = serializer.validated_data
    payment_hash = payload['payment_hash']
    incoming_status = payload['status']

    # ── Fetch payment ──────────────────────────────────────────────────────
    try:
        payment = LightningPayment.objects.get(payment_hash=payment_hash)
    except LightningPayment.DoesNotExist:
        logger.warning(f"[payment_webhook_api] Unknown payment_hash: {payment_hash}")
        return Response(
            {'message': 'Payment not found.'},
            status=status.HTTP_404_NOT_FOUND
        )

    # ── Idempotency check ──────────────────────────────────────────────────
    if payment.status in (
        LightningPayment.Status.SETTLED,
        LightningPayment.Status.FAILED,
        LightningPayment.Status.EXPIRED,
    ):
        logger.info(f"[payment_webhook_api] Already processed: {payment_hash}")
        return Response(
            {'message': 'Already processed.'},
            status=status.HTTP_200_OK
        )

    # ── Update payment status ──────────────────────────────────────────────
    if incoming_status == 'settled':
        payment.mark_settled(
            preimage=payload.get('payment_preimage', ''),
            offramp_ref=payload.get('offramp_reference', ''),
        )
        if payload.get('offramp_status'):
            payment.offramp_status = payload['offramp_status']
            payment.save(update_fields=['offramp_status'])

    elif incoming_status == 'failed':
        payment.mark_failed(reason=payload.get('failure_reason', ''))

    elif incoming_status == 'expired':
        payment.status = LightningPayment.Status.EXPIRED
        payment.save(update_fields=['status', 'updated_at'])

    # Store raw provider payload for audit
    if payload.get('raw'):
        payment.raw_response = payload['raw']
        payment.save(update_fields=['raw_response'])

    logger.info(f"[payment_webhook_api] Payment {payment_hash} → {incoming_status}")

    return Response(
        {'message': f'Payment marked as {incoming_status}.'},
        status=status.HTTP_200_OK
    )


# ─────────────────────────────────────────────────────────────────────────────
# 3. List payments
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAnalystOrAbove])
def list_payments_api(request):
    """
    GET /api/lightning/payments/
    List all Lightning payments for the requesting user's bank.
    Supports ?status=settled|pending|failed|expired|sent filter.
    """
    try:
        bank = Bank.objects.get(user=request.user)
    except Bank.DoesNotExist:
        return Response(
            {'message': 'Bank not found.'},
            status=status.HTTP_404_NOT_FOUND
        )

    payments = LightningPayment.objects.filter(bank=bank).order_by('-created_at')

    # Optional status filter
    status_filter = request.query_params.get('status')
    if status_filter:
        payments = payments.filter(status=status_filter)

    serializer = LightningPaymentListSerializer(payments, many=True)
    return Response({
        'message': 'Payments retrieved successfully.',
        'count': payments.count(),
        'data': serializer.data,
    }, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────────────────────────────────────
# 4. Payment detail
# ─────────────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAnalystOrAbove])
def payment_detail_api(request, payment_id):
    """
    GET /api/lightning/payments/<payment_id>/
    Retrieve full detail of a single payment.
    Scoped to the requesting user's bank.
    """
    try:
        bank = Bank.objects.get(user=request.user)
    except Bank.DoesNotExist:
        return Response(
            {'message': 'Bank not found.'},
            status=status.HTTP_404_NOT_FOUND
        )

    try:
        payment = LightningPayment.objects.get(pk=payment_id, bank=bank)
    except LightningPayment.DoesNotExist:
        return Response(
            {'message': 'Payment not found.'},
            status=status.HTTP_404_NOT_FOUND
        )

    return Response({
        'message': 'Payment retrieved successfully.',
        'data': LightningPaymenDetailstSerializer(payment).data,
    }, status=status.HTTP_200_OK)
