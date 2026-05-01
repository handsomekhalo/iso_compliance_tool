import secrets
from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User  # Use Django's built-in User



class ISOProfile(models.Model):
    """
    Defines how a bank uses ISO 20022.
    One profile per message type / ruleset.
    """
    name = models.CharField(max_length=100)           # e.g. SWIFT_CBPR_PLUS
    message_type = models.CharField(max_length=20)    # pacs.008, camt.053
    version = models.CharField(max_length=10, default="001.08")
    description = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)     # FIX: was missing, referenced in Bank.save()
 
    # Remittance rules
    requires_structured_remittance = models.BooleanField(default=False)
    allows_unstructured_remittance = models.BooleanField(default=True)
    max_remittance_length = models.IntegerField(default=140)
 
    # Validation strictness
    strict_schema_validation = models.BooleanField(default=True)
 
    created_at = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        verbose_name = "ISO Profile"
        verbose_name_plural = "ISO Profiles"
        ordering = ["-created_at"]
 
    def __str__(self):
        return f"{self.name} ({self.message_type})"
 
 
class Bank(models.Model):
    """
    Bank partner for RandRail platform.
    System-managed compliance entity.
    """
    # Core identity
    name = models.CharField(max_length=200)
    contact_email = models.EmailField(unique=True)
    bic = models.CharField(                           # FIX: was missing, referenced in serializers
        max_length=11,
        blank=True,
        null=True,
        help_text="Bank Identifier Code (SWIFT BIC), e.g. ABSAZAJJ"
    )
 
    # Status
    is_active = models.BooleanField(default=True)     # FIX: was missing, referenced in serializers + views
 
    # Auth / access
    api_key = models.CharField(max_length=64, unique=True, blank=True)
 
    # Platform linkage
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="bank"
    )
 
    # Compliance (system-controlled)
    iso_profile = models.ForeignKey(
        "ISOProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="banks"
    )
 
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
 
    class Meta:
        verbose_name = "Bank"
        verbose_name_plural = "Banks"
        ordering = ["-created_at"]
 
    def __str__(self):
        return self.name
 
    def save(self, *args, **kwargs):
        """
        System-enforced defaults:
        - Generate API key on first save
        - Auto-assign default ISO profile if none set
        """
        if not self.api_key:
            self.api_key = self.generate_api_key()
 
        if not self.iso_profile:
            # FIX: now safe — is_active exists on ISOProfile
            self.iso_profile = (
                ISOProfile.objects
                .filter(is_default=True, is_active=True)
                .order_by("id")
                .first()
            )
 
        super().save(*args, **kwargs)
 
    @staticmethod
    def generate_api_key():
        """Generate a secure, URL-safe API key."""
        return f"rr_{secrets.token_urlsafe(32)}"
 
 
class ISOReconciliationLog(models.Model):
    """Track ISO 20022 reconciliation attempts."""
 
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE, related_name='reconciliations')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    filename = models.CharField(max_length=255)
    total_transactions = models.IntegerField(default=0)
    mismatches = models.IntegerField(default=0)
    xrpl_hash = models.CharField(max_length=255, blank=True, null=True)
 
    # Audit trail
    raw_xml = models.TextField(blank=True)
    result_json = models.JSONField(default=dict)
    processing_time_ms = models.IntegerField(null=True, blank=True)
 
    iso_profile = models.ForeignKey(
        ISOProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
 
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
    file_url = models.CharField(max_length=1024)      # Backblaze URL
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_size_bytes = models.BigIntegerField(null=True, blank=True)
    file_hash = models.CharField(max_length=255, blank=True, null=True)   # SHA256
    log = models.ForeignKey(ISOReconciliationLog, on_delete=models.CASCADE, related_name="documents")
 
    def __str__(self):
        return self.file_name
 
 
class ZARPMintEvent(models.Model):
    """Track stablecoin minting events (PANZAR)."""
 
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE, related_name='mint_events', null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    token_id = models.CharField(max_length=255, unique=True)
    stellar_tx_hash = models.CharField(max_length=64, blank=True, null=True)
    escrow_verified = models.BooleanField(default=False)
    escrow_reference = models.CharField(max_length=255, blank=True, null=True)
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
    """Track stablecoin redemptions (PANZAR)."""
 
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
    """KYC-verified test users for sandbox."""
 
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
    kyc_reference = models.CharField(max_length=255, blank=True, null=True)   # Smile ID ref
    kyc_verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
 
    # Sandbox compliance
    consent_given = models.BooleanField(default=False)
    consent_date = models.DateTimeField(null=True, blank=True)
 
    def __str__(self):
        return f"{self.email} ({self.kyc_status})"
 
 
class AMLAlert(models.Model):
    """Track Chainalysis KYT alerts for compliance."""
 
    transaction_type = models.CharField(max_length=20, choices=[('mint', 'Mint'), ('burn', 'Burn')])
    transaction_id = models.CharField(max_length=255)
    alert_level = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('severe', 'Severe'),
        ]
    )
    risk_score = models.DecimalField(max_digits=5, decimal_places=2)   # 0.00–100.00
    details = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)
 
    class Meta:
        ordering = ['-created_at']
 
    def __str__(self):
        return f"{self.alert_level.upper()} - {self.transaction_id[:8]}... (Score: {self.risk_score})"
 
 
class ISOFieldRule(models.Model):
    """
    Dynamic validation rules per ISO profile.
    Stored in DB so rules can be configured without code changes.
    """
    iso_profile = models.ForeignKey(
        ISOProfile,
        on_delete=models.CASCADE,
        related_name="field_rules"
    )
    field_path = models.CharField(max_length=255)     # e.g. "CdtTrfTxInf.Amt"
    required = models.BooleanField(default=False)
    max_length = models.IntegerField(null=True, blank=True)
    regex = models.CharField(max_length=255, blank=True)
    weight = models.IntegerField(                     # FIX: needed for dynamic scoring
        default=1,
        help_text="Violation severity weight for compliance score calculation (1=low, 5=critical)"
    )
 
    class Meta:
        verbose_name = "ISO Field Rule"
        verbose_name_plural = "ISO Field Rules"
        unique_together = [("iso_profile", "field_path")]
 
    def __str__(self):
        return f"{self.iso_profile.name} → {self.field_path} (weight={self.weight})"

"""
STEP 1 of 4 — ADD TO models.py
===============================
Paste this at the bottom of compliance_management/models.py.
It adds RoleName choices and the UserRole model.
After pasting, run:
    python manage.py makemigrations compliance_management
    python manage.py migrate compliance_management
"""

class RoleName(models.TextChoices):
    """
    Platform roles in ascending access order.

    END_USER          B2C sandbox users — remittance only, no dashboard access
    ANALYST           Upload files, view reconciliation results
    AUDITOR           Read-only + export reports, no uploads
    INSTITUTION_ADMIN Full access scoped to their bank
    SUPER_ADMIN       You (Titus) — cross-bank, full platform
    """
    END_USER          = "end_user",          "End User"
    ANALYST           = "analyst",           "Analyst"
    AUDITOR           = "auditor",           "Auditor"
    INSTITUTION_ADMIN = "institution_admin", "Institution Admin"
    SUPER_ADMIN       = "super_admin",       "Super Admin"


class UserRole(models.Model):
    """
    Links a Django User to a role, scoped to a Bank.
    SUPER_ADMIN rows have bank=None (platform-wide access).
    All other roles must have a bank assigned.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="role"
    )
    role = models.CharField(
        max_length=30,
        choices=RoleName.choices,
        default=RoleName.ANALYST
    )
    bank = models.ForeignKey(
        "Bank",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="user_roles",
        help_text="Null only for SUPER_ADMIN"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Role"
        verbose_name_plural = "User Roles"

    def __str__(self):
        bank_name = self.bank.name if self.bank else "Platform"
        return f"{self.user.email} — {self.role} @ {bank_name}"

    # --- convenience helpers (no DB queries) ----------------------------

    def is_super_admin(self):
        return self.role == RoleName.SUPER_ADMIN

    def is_institution_admin(self):
        return self.role in [RoleName.INSTITUTION_ADMIN, RoleName.SUPER_ADMIN]

    def can_upload(self):
        """Analysts and above can upload ISO files."""
        return self.role in [
            RoleName.ANALYST,
            RoleName.INSTITUTION_ADMIN,
            RoleName.SUPER_ADMIN,
        ]

    def can_export(self):
        """Auditors and above can export PDF/CSV reports."""
        return self.role in [
            RoleName.AUDITOR,
            RoleName.ANALYST,
            RoleName.INSTITUTION_ADMIN,
            RoleName.SUPER_ADMIN,
        ]

    def can_manage_rules(self):
        """Only admins can create/edit ISOFieldRules."""
        return self.role in [
            RoleName.INSTITUTION_ADMIN,
            RoleName.SUPER_ADMIN,
        ]

    def can_manage_users(self):
        """Only admins can invite/remove users from their bank."""
        return self.role in [
            RoleName.INSTITUTION_ADMIN,
            RoleName.SUPER_ADMIN,
        ]
