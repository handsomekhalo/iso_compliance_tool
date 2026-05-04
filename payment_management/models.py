from django.db import models

# Create your models here.
class LightningPayment(models.Model):
    """
    Records a Lightning Network payment initiated via RandRail.
    Sits alongside reconciliation as the B2C remittance rail.
    """

    class Status(models.TextChoices):
        PENDING   = 'pending',   'Pending'
        SENT      = 'sent',      'Sent'
        SETTLED   = 'settled',   'Settled'
        FAILED    = 'failed',    'Failed'
        EXPIRED   = 'expired',   'Expired'

    class Direction(models.TextChoices):
        OUTBOUND = 'outbound', 'Outbound'  # RandRail → recipient
        INBOUND  = 'inbound',  'Inbound'   # recipient → RandRail

    # ── Relationships ──────────────────────────────────────────────────────
    bank         = models.ForeignKey(Bank, on_delete=models.PROTECT, related_name='lightning_payments')
    initiated_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='lightning_payments')

    # ── Payment details ────────────────────────────────────────────────────
    amount_zar   = models.DecimalField(max_digits=12, decimal_places=2)       # ZAR amount
    amount_sats  = models.BigIntegerField(null=True, blank=True)               # satoshis (set after BTC conversion)
    exchange_rate= models.DecimalField(max_digits=18, decimal_places=8, null=True, blank=True)  # ZAR/BTC rate at time of payment

    direction    = models.CharField(max_length=10, choices=Direction.choices, default=Direction.OUTBOUND)
    status       = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)

    # ── Lightning Network fields ───────────────────────────────────────────
    payment_request  = models.TextField(blank=True)         # BOLT11 invoice string
    payment_hash     = models.CharField(max_length=255, blank=True, db_index=True)  # LND payment hash
    payment_preimage = models.CharField(max_length=255, blank=True)  # proof of payment

    # ── Off-ramp fields (MoneyBadger/VALR) ────────────────────────────────
    offramp_provider     = models.CharField(max_length=50, blank=True)   # 'moneybadger' | 'valr'
    offramp_reference    = models.CharField(max_length=255, blank=True)  # provider's reference ID
    offramp_status       = models.CharField(max_length=50, blank=True)   # provider's own status string
    recipient_account    = models.CharField(max_length=255, blank=True)  # destination (phone, account no, lightning address)

    # ── Audit fields ───────────────────────────────────────────────────────
    xrpl_hash        = models.CharField(max_length=255, blank=True)  # audit fingerprint same as reconciliation
    failure_reason   = models.TextField(blank=True)
    raw_response     = models.JSONField(null=True, blank=True)        # full LND/MoneyBadger response stored for audit

    # ── Timestamps ────────────────────────────────────────────────────────
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)
    settled_at   = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Lightning Payment"
        verbose_name_plural = "Lightning Payments"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['bank', 'status']),
            models.Index(fields=['payment_hash']),
        ]

    def __str__(self):
        return f"{self.bank.name} | {self.amount_zar} ZAR | {self.status} | {self.created_at:%Y-%m-%d}"

    def mark_settled(self, preimage, offramp_ref=''):
        from django.utils import timezone
        self.status = self.Status.SETTLED
        self.payment_preimage = preimage
        self.offramp_reference = offramp_ref
        self.settled_at = timezone.now()
        self.save(update_fields=['status', 'payment_preimage', 'offramp_reference', 'settled_at', 'updated_at'])

    def mark_failed(self, reason=''):
        self.status = self.Status.FAILED
        self.failure_reason = reason
        self.save(update_fields=['status', 'failure_reason', 'updated_at'])