# payment_management/serializers.py

from rest_framework import serializers
from payment_management.models import LightningPayment


class InitiatePaymentSerializer(serializers.Serializer):
    """
    Validates the incoming send request from the frontend.
    No model binding — just validates input.
    """
    amount_zar       = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=1)
    recipient_account= serializers.CharField(max_length=255)  # phone, lightning address, account no
    offramp_provider = serializers.ChoiceField(
        choices=['moneybadger', 'valr'],
        default='moneybadger'
    )
    direction        = serializers.ChoiceField(
        choices=['outbound', 'inbound'],
        default='outbound'
    )
    description      = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def validate_amount_zar(self, value):
        # Minimum ZAR 1, maximum ZAR 50,000 (sandbox limit)
        if value > 50000:
            raise serializers.ValidationError(
                "Amount exceeds sandbox limit of R50,000 per transaction."
            )
        return value

    def validate_recipient_account(self, value):
        if not value.strip():
            raise serializers.ValidationError("Recipient account cannot be empty.")
        return value.strip()


class LightningPaymentListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for list views.
    """
    bank_name    = serializers.CharField(source='bank.name', read_only=True)
    initiated_by_email = serializers.CharField(source='initiated_by.email', read_only=True)

    class Meta:
        model  = LightningPayment
        fields = [
            'id',
            'bank_name',
            'initiated_by_email',
            'amount_zar',
            'amount_sats',
            'direction',
            'status',
            'offramp_provider',
            'recipient_account',
            'payment_hash',
            'created_at',
            'settled_at',
        ]


class LightningPaymentSerializer(serializers.ModelSerializer):
    """
    Full detail serializer — used for retrieve, send response, webhook response.
    """
    bank_name          = serializers.CharField(source='bank.name', read_only=True)
    initiated_by_email = serializers.CharField(source='initiated_by.email', read_only=True)

    class Meta:
        model  = LightningPayment
        fields = [
            'id',
            'bank_name',
            'initiated_by_email',
            'amount_zar',
            'amount_sats',
            'exchange_rate',
            'direction',
            'status',
            'payment_request',
            'payment_hash',
            'payment_preimage',
            'offramp_provider',
            'offramp_reference',
            'offramp_status',
            'recipient_account',
            'xrpl_hash',
            'failure_reason',
            'created_at',
            'updated_at',
            'settled_at',
        ]
        read_only_fields = fields  # all read-only — mutations go through service layer


class WebhookPayloadSerializer(serializers.Serializer):
    """
    Validates incoming webhook payload from LND / MoneyBadger.
    Both providers send slightly different shapes — we normalise here.
    """
    payment_hash     = serializers.CharField(max_length=255)
    payment_preimage = serializers.CharField(max_length=255, required=False, allow_blank=True)
    status           = serializers.ChoiceField(choices=['settled', 'failed', 'expired'])
    offramp_reference= serializers.CharField(max_length=255, required=False, allow_blank=True, default='')
    offramp_status   = serializers.CharField(max_length=50,  required=False, allow_blank=True, default='')
    failure_reason   = serializers.CharField(max_length=500, required=False, allow_blank=True, default='')
    raw              = serializers.JSONField(required=False)  # full provider payload stored as-is



class LightningPaymenDetailstSerializer(serializers.ModelSerializer):
    """
    Full detail serializer — used for retrieve, send response, webhook response.
    """
    bank_name          = serializers.CharField(source='bank.name', read_only=True)
    initiated_by_email = serializers.CharField(source='initiated_by.email', read_only=True)

    class Meta:
        model  = LightningPayment
        fields = [
            'id',
            'bank_name',
            'initiated_by_email',
            'amount_zar',
            'amount_sats',
            'exchange_rate',
            'direction',
            'status',
            'payment_request',
            'payment_hash',
            'payment_preimage',
            'offramp_provider',
            'offramp_reference',
            'offramp_status',
            'recipient_account',
            'xrpl_hash',
            'failure_reason',
            'created_at',
            'updated_at',
            'settled_at',
        ]
        read_only_fields = fields  # all read-only — mutations go through service layer

