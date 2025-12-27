from rest_framework import serializers
from django.contrib.auth.models import User

from compliance_management.models import AMLAlert, Bank, ISODocument, ISOProfile, ISOReconciliationLog, SandboxUser, ZARPBurnEvent, ZARPMintEvent


class UserModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "is_staff", "is_superuser"]


# class BankSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Bank
#         fields = "__all__"



class BankRegistrationSerializer(serializers.Serializer):
    """Serializer for bank registration"""
    bank_name = serializers.CharField(max_length=200)
    contact_email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    
    def validate_contact_email(self, value):
        """Check if email already exists"""
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

        # ✅ Get default ISO profile
        iso_profile = ISOProfile.objects.filter(is_default=True).first()

        if not iso_profile:
            raise serializers.ValidationError(
                "No default ISO profile configured in system"
            )

        bank = Bank.objects.create(
            name=validated_data['bank_name'],
            contact_email=validated_data['contact_email'],
            user=user,
            iso_profile=iso_profile   # ✅ ASSIGNED HERE
        )

        return bank

    
    # def create(self, validated_data):
    #     """Create bank and associated user"""
    #     # Create Django User for login
    #     user = User.objects.create_user(
    #         username=validated_data['contact_email'],  # Use email as username
    #         email=validated_data['contact_email'],
    #         password=validated_data['password']
    #     )
        
    #     # Create Bank
    #     bank = Bank.objects.create(
    #         name=validated_data['bank_name'],
    #         contact_email=validated_data['contact_email'],
    #         user=user
    #     )
        
    #     return bank

class ISOProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ISOProfile
        fields = "__all__"


class BankSResponseSerializer(serializers.ModelSerializer):
    iso_profile = ISOProfileSerializer()

    class Meta:
        model = Bank
        fields = [
            "id",
            "bank_name",
            "bic",
            "iso_profile",
        ]


class BankLoginSerializer(serializers.Serializer):
    """Serializer for bank login"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)



class BankDetailSerializer(serializers.ModelSerializer):
    """Serializer for bank details (for /api/auth/me/)"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    
    class Meta:
        model = Bank
        fields = [
            'id',
            'name',
            'contact_email',
            'api_key',
            'is_active',
            'created_at',
            'user_id',
            'user_email'
        ]
        read_only_fields = ['id', 'api_key', 'created_at']


class BankRegistrationResponseSerializer(serializers.ModelSerializer):
    """Response serializer after successful registration"""
    bank_id = serializers.IntegerField(source='id', read_only=True)
    
    class Meta:
        model = Bank
        fields = ['bank_id', 'name', 'contact_email', 'api_key']



class ISOReconciliationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ISOReconciliationLog
        fields = "__all__"


# reconciliation/serializers.py

# ADD these to your existing serializers file:

class ISODocumentSerializer(serializers.ModelSerializer):
    """Serializer for ISO document file metadata"""
    bank_name = serializers.CharField(source='bank.name', read_only=True)
    log_id = serializers.IntegerField(source='log.id', read_only=True)
    log_filename = serializers.CharField(source='log.filename', read_only=True)
    
    class Meta:
        model = ISODocument
        fields = [
            'id',
            'bank_name',
            'file_name',
            # 'file_url',
            'uploaded_at',
            'file_size_bytes',
            'file_hash',
            'log_id',
            'log_filename'
        ]
        read_only_fields = ['id', 'uploaded_at', 'file_hash']



# class UploadFileOnlySerializer(serializers.Serializer):
#     """
#     Serializer only for validating the uploaded file and bank name input.
#     """
#     # Use a FileField to handle the uploaded file object (InMemoryUploadedFile)
#     file_name = serializers.FileField(label="ISO Document File")
    
#     # Use a CharField for the bank name if you are sending it in the POST data
#     bank_name = serializers.CharField(max_length=255, required=False) # Or whatever field you pass

#     # Optional: If you need to check if the file is an XML (or specific extension)
#     def validate_file_name(self, value):
#         # if not value.name.lower().endswith(('.xml', '.xlsx')): # Adjust extensions as needed
#         if not value.name.lower().endswith( '.xml', '.xlsx', '.xls', '.csv', '.json'): # Adjust extensions as needed
          
#             raise serializers.ValidationError("Only XML or XLSX files are allowed.")
#         return value

class UploadFileOnlySerializer(serializers.Serializer):
    """
    Serializer for validating uploaded ISO 20022 files.
    Accepts: XML, XLSX, XLS, CSV, JSON formats
    """
    # FileField to handle the uploaded file object
    file_name = serializers.FileField(label="ISO Document File")
    
    # Optional bank name (if sent in POST data)
    bank_name = serializers.CharField(max_length=255, required=False)

    def validate_file_name(self, value):
        """
        Validate file extension and size
        """
        # Get file extension
        filename = value.name.lower()
        
        # Allowed ISO 20022 file formats
        allowed_extensions = ('.xml', '.xlsx', '.xls', '.csv', '.json')
        
        # Check if file has valid extension
        if not filename.endswith(allowed_extensions):
            raise serializers.ValidationError(
                f"Invalid file format. Allowed formats: XML, XLSX, XLS, CSV, JSON. "
                f"Got: {filename.split('.')[-1].upper()}"
            )
        
        # Check file size (max 10MB for sandbox)
        max_size = 10 * 1024 * 1024  # 10MB in bytes
        if value.size > max_size:
            size_mb = value.size / (1024 * 1024)
            raise serializers.ValidationError(
                f"File too large. Maximum size: 10MB. Your file: {size_mb:.2f}MB"
            )
        
        # Check if file is empty
        if value.size == 0:
            raise serializers.ValidationError("Uploaded file is empty")
        
        return value

class GetISODocumentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing documents"""
    bank_name = serializers.CharField(source='bank.name', read_only=True)
    file_size_mb = serializers.SerializerMethodField()
    
    class Meta:
        model = ISODocument
        fields = [
            'id',
            'bank_name',
            'file_name',
            'file_url',
            'uploaded_at',
            'file_size_mb'
        ]
    
    def get_file_size_mb(self, obj):
        """Convert bytes to MB for display"""
        if obj.file_size_bytes:
            return round(obj.file_size_bytes / (1024 * 1024), 2)
        return 0


class ISOReconciliationUploadSerializer(serializers.Serializer):
    """Serializer for XML file upload"""
    file = serializers.FileField()
    
    def validate_file(self, value):
        """Validate uploaded file"""
        # Check file extension
        if not value.name.endswith('.xml'):
            raise serializers.ValidationError("Only XML files are accepted")
        
        # Check file size (max 10MB for sandbox)
        if value.size > 10 * 1024 * 1024:  # 10MB
            raise serializers.ValidationError("File size must be less than 10MB")
        
        return value


class ISOReconciliationListSerializer(serializers.ModelSerializer):
    """Serializer for listing reconciliations (summary view)"""
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
            'status'
        ]
    
    def get_status(self, obj):
        """Determine status based on mismatches"""
        if obj.mismatches == 0:
            return 'perfect'
        elif obj.mismatches <= 5:
            return 'good'
        elif obj.mismatches <= 20:
            return 'warning'
        else:
            return 'critical'


class ISOReconciliationDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed reconciliation view"""
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
            'processing_time_ms'
        ]


class GetISOReconciliationStatsSerializer(serializers.Serializer):
    """Serializer for dashboard statistics"""
    total_reconciliations = serializers.IntegerField()
    total_transactions_processed = serializers.IntegerField()
    total_mismatches = serializers.IntegerField()
    average_accuracy = serializers.FloatField()
    files_processed_today = serializers.IntegerField()

class ZARPMintEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ZARPMintEvent
        fields = "__all__"


class ZARPBurnEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ZARPBurnEvent
        fields = "__all__"


class SandboxUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = SandboxUser
        fields = "__all__"


class AMLAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = AMLAlert
        fields = "__all__"


class BankSerializer(serializers.ModelSerializer):
    iso_profile = ISOProfileSerializer(read_only=True)

    class Meta:
        model = Bank
        fields = [
            "id",
            "name",
            "contact_email",
            "api_key",
            "iso_profile",
        ]
