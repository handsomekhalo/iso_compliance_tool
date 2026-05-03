from rest_framework import serializers
from django.contrib.auth.models import User

from compliance_management.models import AMLAlert, Bank, ISODocument, ISOProfile, ISOReconciliationLog, SandboxUser, UserRole, ZARPBurnEvent, ZARPMintEvent



from rest_framework import serializers
from django.contrib.auth.models import User
from compliance_management.models import (
    AMLAlert, Bank, ISODocument, ISOFieldRule,
    ISOProfile, ISOReconciliationLog,
    SandboxUser, ZARPBurnEvent, ZARPMintEvent
)


class UserModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "is_staff", "is_superuser"]


# ---------------------------------------------------------------------------
# ISO Profile
# ---------------------------------------------------------------------------

class ISOProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ISOProfile
        fields = "__all__"


# ---------------------------------------------------------------------------
# ISOFieldRule — needed for dynamic scoring CRUD endpoint
# ---------------------------------------------------------------------------

class ISOFieldRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ISOFieldRule
        fields = ["id", "field_path", "required", "max_length", "regex", "weight"]


# ---------------------------------------------------------------------------
# Bank registration / login / detail
# ---------------------------------------------------------------------------

class BankRegistrationSerializer(serializers.Serializer):
    """Validate and create a new bank + linked Django user."""

    bank_name = serializers.CharField(max_length=200)
    contact_email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    bic = serializers.CharField(                          # FIX: exposed in registration
        max_length=11,
        required=False,
        allow_blank=True,
        help_text="Optional SWIFT BIC, e.g. ABSAZAJJ"
    )

    def validate_contact_email(self, value):
        if Bank.objects.filter(contact_email=value).exists():
            raise serializers.ValidationError("A bank with this email already exists.")
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already registered.")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['contact_email'],
            email=validated_data['contact_email'],
            password=validated_data['password']
        )

        iso_profile = ISOProfile.objects.filter(is_default=True, is_active=True).first()
        if not iso_profile:
            raise serializers.ValidationError("No default ISO profile configured in system.")

        bank = Bank.objects.create(
            name=validated_data['bank_name'],
            contact_email=validated_data['contact_email'],
            bic=validated_data.get('bic', ''),         # FIX: persist bic if provided
            user=user,
            iso_profile=iso_profile
        )
        return bank


class BankLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class BankDetailSerializer(serializers.ModelSerializer):
    """Full bank detail — used by /api/auth/me/"""

    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    iso_profile = ISOProfileSerializer(read_only=True)

    class Meta:
        model = Bank
        fields = [
            'id',
            'name',
            'contact_email',
            'bic',           # FIX: now exists on model
            'api_key',
            'is_active',     # FIX: now exists on model
            'iso_profile',
            'created_at',
            'user_id',
            'user_email',
        ]
        read_only_fields = ['id', 'api_key', 'created_at']


class BankRegistrationResponseSerializer(serializers.ModelSerializer):
    """Slim response after successful registration."""

    bank_id = serializers.IntegerField(source='id', read_only=True)

    class Meta:
        model = Bank
        fields = ['bank_id', 'name', 'contact_email', 'bic', 'api_key']


class BankSerializer(serializers.ModelSerializer):
    """Used in login response and general bank context."""

    iso_profile = ISOProfileSerializer(read_only=True)

    class Meta:
        model = Bank
        fields = [
            "id",
            "name",
            "contact_email",
            "bic",           # FIX: now exists on model
            "api_key",
            "is_active",     # FIX: now exists on model
            "iso_profile",
        ]


# FIX: removed BankSResponseSerializer — it referenced 'bank_name' (wrong field name,
# should be 'name') and 'bic' which didn't exist. BankSerializer above replaces it.


# ---------------------------------------------------------------------------
# ISO Documents
# ---------------------------------------------------------------------------

class ISODocumentSerializer(serializers.ModelSerializer):
    bank_name = serializers.CharField(source='bank.name', read_only=True)
    log_id = serializers.IntegerField(source='log.id', read_only=True)
    log_filename = serializers.CharField(source='log.filename', read_only=True)

    class Meta:
        model = ISODocument
        fields = [
            'id',
            'bank_name',
            'file_name',
            'uploaded_at',
            'file_size_bytes',
            'file_hash',
            'log_id',
            'log_filename',
        ]
        read_only_fields = ['id', 'uploaded_at', 'file_hash']


class GetISODocumentListSerializer(serializers.ModelSerializer):
    bank_name = serializers.CharField(source='bank.name', read_only=True)
    file_size_mb = serializers.SerializerMethodField()

    class Meta:
        model = ISODocument
        fields = ['id', 'bank_name', 'file_name', 'file_url', 'uploaded_at', 'file_size_mb']

    def get_file_size_mb(self, obj):
        if obj.file_size_bytes:
            return round(obj.file_size_bytes / (1024 * 1024), 2)
        return 0


# ---------------------------------------------------------------------------
# File upload validation
# ---------------------------------------------------------------------------

class UploadFileOnlySerializer(serializers.Serializer):
    """Validate uploaded ISO 20022 files. Accepts XML, XLSX, XLS, CSV, JSON."""

    file_name = serializers.FileField(label="ISO Document File")
    bank_name = serializers.CharField(max_length=255, required=False)

    def validate_file_name(self, value):
        filename = value.name.lower()
        allowed_extensions = ('.xml', '.xlsx', '.xls', '.csv', '.json')

        if not filename.endswith(allowed_extensions):
            raise serializers.ValidationError(
                f"Invalid file format. Allowed: XML, XLSX, XLS, CSV, JSON. "
                f"Got: {filename.split('.')[-1].upper()}"
            )

        max_size = 10 * 1024 * 1024  # 10MB
        if value.size > max_size:
            size_mb = value.size / (1024 * 1024)
            raise serializers.ValidationError(
                f"File too large. Maximum: 10MB. Your file: {size_mb:.2f}MB"
            )

        if value.size == 0:
            raise serializers.ValidationError("Uploaded file is empty.")

        return value


# ---------------------------------------------------------------------------
# Reconciliation logs
# ---------------------------------------------------------------------------

class ISOReconciliationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ISOReconciliationLog
        fields = "__all__"


class ISOReconciliationListSerializer(serializers.ModelSerializer):
    """Summary list view — used in dashboard table."""

    bank_name = serializers.CharField(source='bank.name', read_only=True)
    accuracy_rate = serializers.FloatField(read_only=True)
    status = serializers.SerializerMethodField()

    class Meta:
        model = ISOReconciliationLog
        fields = [
            'id',
            'bank_name',
            'filename',
            'uploaded_at',
            'total_transactions',
            'mismatches',
            'accuracy_rate',
            'xrpl_hash',
            'processing_time_ms',
            'status',
        ]

    def get_status(self, obj):
        """
        FIX: thresholds should come from ISOProfile config eventually,
        but for now they are readable constants, not magic numbers scattered
        across the codebase.
        """
        PERFECT = 0
        GOOD_MAX = 5
        WARNING_MAX = 20

        if obj.mismatches == PERFECT:
            return 'perfect'
        elif obj.mismatches <= GOOD_MAX:
            return 'good'
        elif obj.mismatches <= WARNING_MAX:
            return 'warning'
        else:
            return 'critical'


class ISOReconciliationDetailSerializer(serializers.ModelSerializer):
    """Full detail view including raw result JSON."""

    bank_name = serializers.CharField(source='bank.name', read_only=True)
    bank_id = serializers.IntegerField(source='bank.id', read_only=True)
    accuracy_rate = serializers.FloatField(read_only=True)

    class Meta:
        model = ISOReconciliationLog
        fields = [
            'id',
            'bank_id',
            'bank_name',
            'filename',
            'uploaded_at',
            'total_transactions',
            'mismatches',
            'accuracy_rate',
            'xrpl_hash',
            'raw_xml',
            'result_json',
            'processing_time_ms',
        ]


class GetISOReconciliationStatsSerializer(serializers.Serializer):
    """Dashboard statistics."""

    total_reconciliations = serializers.IntegerField()
    total_transactions_processed = serializers.IntegerField()
    total_mismatches = serializers.IntegerField()
    average_accuracy = serializers.FloatField()
    files_processed_today = serializers.IntegerField()


# ---------------------------------------------------------------------------
# Stablecoin events
# ---------------------------------------------------------------------------

class ZARPMintEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ZARPMintEvent
        fields = "__all__"


class ZARPBurnEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ZARPBurnEvent
        fields = "__all__"


# ---------------------------------------------------------------------------
# Sandbox users & AML
# ---------------------------------------------------------------------------

class SandboxUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = SandboxUser
        fields = "__all__"


class AMLAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = AMLAlert
        fields = "__all__"

class UserRoleSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    bank_name = serializers.CharField(source='bank.name', read_only=True, allow_null=True)

    class Meta:
        model = UserRole
        fields = ['id', 'user_email', 'role', 'bank_name', 'created_at']
        read_only_fields = ['id', 'created_at']


class InviteUserSerializer(serializers.Serializer):
    # "\"\"Used by institution admins to invite a new user to their bank.\"\"\"
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=[
        ('analyst', 'Analyst'),
        ('auditor', 'Auditor'),
        ('institution_admin', 'Institution Admin'),
    ])
    password = serializers.CharField(write_only=True, min_length=8)

