import secrets
from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User  # Use Django's built-in User

# class Bank(models.Model):
#     """Simple bank partner for sandbox testing"""
#     name = models.CharField(max_length=200)
#     contact_email = models.EmailField()
#     api_key = models.CharField(max_length=255, unique=True)
#     is_active = models.BooleanField(default=True)
#     created_at = models.DateTimeField(auto_now_add=True)
    
#     def __str__(self):
#         return self.name
class Bank(models.Model):
    """Bank partner for RandRail platform"""
    name = models.CharField(max_length=200)
    contact_email = models.EmailField(unique=True)
    api_key = models.CharField(max_length=64, unique=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Link to Django User for dashboard login
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Auto-generate API key if not exists
        if not self.api_key:
            self.api_key = self.generate_api_key()
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_api_key():
        """Generate unique API key"""
        return f"rr_{secrets.token_urlsafe(32)}"
    
    class Meta:
        verbose_name = "Bank"
        verbose_name_plural = "Banks"
        ordering = ['-created_at']

class ISOReconciliationLog(models.Model):
    """Track ISO 20022 reconciliation attempts"""
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE, related_name='reconciliations')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    filename = models.CharField(max_length=255)
    total_transactions = models.IntegerField(default=0)
    mismatches = models.IntegerField(default=0)
    xrpl_hash = models.CharField(max_length=255, blank=True, null=True)  # Audit trail
    raw_xml = models.TextField(blank=True)  # Store for review
    result_json = models.JSONField(default=dict)  # Detailed results
    processing_time_ms = models.IntegerField(null=True, blank=True)  # Performance metric
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.bank.name} - {self.filename} ({self.mismatches} mismatches)"
    
    @property
    def accuracy_rate(self):
        if self.total_transactions == 0:
            return 0
        return ((self.total_transactions - self.mismatches) / self.total_transactions) * 100


class ISODocument(models.Model):
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE, related_name="iso_documents")
    file_name = models.CharField(max_length=255)
    file_url = models.CharField(max_length=1024)  # Backblaze or S3 URL
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_size_bytes = models.BigIntegerField(null=True, blank=True)
    file_hash = models.CharField(max_length=255, blank=True, null=True)  # SHA256 for audit
    log = models.ForeignKey(ISOReconciliationLog, on_delete=models.CASCADE, related_name="documents")

    def __str__(self):
        return self.file_name


class ZARPMintEvent(models.Model):
    """Track stablecoin minting events - rename to your new coin name"""
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE, related_name='mint_events', null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(max_digits=18, decimal_places=2)  # Increased for larger amounts
    token_id = models.CharField(max_length=255, unique=True)  # Should be unique
    stellar_tx_hash = models.CharField(max_length=64, blank=True, null=True)  # Stellar hashes are 64 chars
    escrow_verified = models.BooleanField(default=False)
    escrow_reference = models.CharField(max_length=255, blank=True, null=True)  # Nedbank ref
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('confirmed', 'Confirmed'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"Mint R{self.amount} - {self.token_id[:8]}... ({self.status})"


class ZARPBurnEvent(models.Model):
    """Track stablecoin redemptions"""
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE, related_name='burn_events', null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    token_id = models.CharField(max_length=255)
    stellar_tx_hash = models.CharField(max_length=64, blank=True, null=True)
    refund_verified = models.BooleanField(default=False)
    refund_reference = models.CharField(max_length=255, blank=True, null=True)
    
    def __str__(self):
        return f"Burn R{self.amount} - {self.token_id[:8]}..."


class SandboxUser(models.Model):
    """KYC-verified test users for sandbox"""
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    kyc_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('verified', 'Verified'),
            ('rejected', 'Rejected'),
        ],
        default='pending'
    )
    kyc_reference = models.CharField(max_length=255, blank=True, null=True)  # Smile ID reference
    kyc_verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # For sandbox compliance tracking
    consent_given = models.BooleanField(default=False)
    consent_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.email} ({self.kyc_status})"


class AMLAlert(models.Model):
    """Track Chainalysis KYT alerts for compliance"""
    transaction_type = models.CharField(max_length=20, choices=[('mint', 'Mint'), ('burn', 'Burn')])
    transaction_id = models.CharField(max_length=255)  # Links to mint/burn event
    alert_level = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('severe', 'Severe'),
        ]
    )
    risk_score = models.DecimalField(max_digits=5, decimal_places=2)  # 0.00 to 100.00
    details = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.alert_level.upper()} - {self.transaction_id[:8]}... (Score: {self.risk_score})"