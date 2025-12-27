import json
import random
import time
from django.utils import timezone # ⬅️ CORRECT
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth.models import User
import chardet
from django.db.models import Sum

import datetime
from datetime import datetime
import json
import random
from requests import Response, request

from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from rest_framework.response import Response
from rest_framework import status


# from rest_framework.decorators import api_view, permission_classes

from rest_framework import (
    status,
    permissions,
    authentication
)

# from rest_framework.decorators import (
#     api_view,
#     authentication_classes,
#     permission_classes
# )

from compliance_management.models import Bank, ISODocument, ISOReconciliationLog
from compliance_management.reconcilliation_util import delete_from_cloud_storage, format_reconciliation_result, generate_xrpl_hash, parse_iso20022_file, parse_iso20022_xml, upload_to_cloud_storage
from compliance_management.views import login




from .serializers import BankDetailSerializer, BankLoginSerializer, BankRegistrationResponseSerializer, BankRegistrationSerializer, BankSerializer, GetISODocumentListSerializer, GetISOReconciliationStatsSerializer, ISODocumentSerializer, ISOReconciliationDetailSerializer, ISOReconciliationListSerializer, UploadFileOnlySerializer, UserModelSerializer


@api_view(["POST"])
@permission_classes((AllowAny,))
def login_api(request):
    """ Login API for user authentication """

    try:
        body = json.loads(request.body)
    except:
        return Response(
            {"status": "error", "message": "Invalid JSON"},
            status=status.HTTP_400_BAD_REQUEST
        )

    email = body.get("email")
    password = body.get("password")

    if not email or not password:
        return Response(
            {"status": "error", "message": "Please provide both email and password"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Authenticate by email (superuser allowed)
    user = authenticate(username=email, password=password)

    if not user:
        return Response(
            {"status": "error", "message": "Invalid Credentials"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not user.is_active:
        return Response(
            {"status": "error", "message": "User is inactive, please contact admin"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    token, _ = Token.objects.get_or_create(user=user)

    # Simple 5-digit OTP (temporary)
    otp = "".join([str(random.randint(0, 9)) for _ in range(5)])

    user.last_login = datetime.now()
    user.save()

    user_serializer = UserModelSerializer(user)

    return Response(
        {
            "status": "success",
            "token": token.key,
            "otp": otp,
            "user": user_serializer.data,
        },
        status=status.HTTP_200_OK,
    )




@api_view(["POST"])
# @permission_classes((AllowAny))
@permission_classes([AllowAny])   # optional — depends on your platform
def register_bank_api(request):
    """
    POST /api/auth/register/
    Register a new bank account
    """

    print('inside API')
    serializer = BankRegistrationSerializer(data=request.data)
    
    if serializer.is_valid():
        bank = serializer.save()
        
        # Create auth token for immediate login (optional)
        token, _ = Token.objects.get_or_create(user=bank.user)
        
        # Response data
        response_serializer = BankRegistrationResponseSerializer(bank)
        
        return Response({
            'message': 'Bank registered successfully',
            'data': response_serializer.data,
            'token': token.key  # Optional: for immediate login
        }, status=status.HTTP_201_CREATED)
    
    return Response({
        'message': 'Registration failed',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


# @api_view(['POST'])
# @permission_classes([AllowAny])
# def login_bank_api(request):
#     """
#     POST /api/auth/login/
#     Login bank user and return token
#     """
#     serializer = BankLoginSerializer(data=request.data)
#     # bank = Bank.objects.select_related("iso_profile").get(user=user)

    
#     if serializer.is_valid():
#         email = serializer.validated_data['email']
#         password = serializer.validated_data['password']
        
#         # Authenticate user (using email as username)
#         try:
#             user = User.objects.get(email=email)
#             # user = authenticate(username=user.username, password=password)
#             user = authenticate(request, username=user.username, password=password)
#         except User.DoesNotExist:
#             user = None
        
#         if user is not None:
#             # Get associated bank
#             try:
#                 bank = Bank.objects.get(user=user)
                
#                 if not bank.is_active:
#                     return Response({
#                         'message': 'Bank account is inactive'
#                     }, status=status.HTTP_403_FORBIDDEN)
                
#                 # Create or get token
#                 token, _ = Token.objects.get_or_create(user=user)
                
#                 # Login user (for session-based auth if needed)
#                 # login(request, user)
                
#                 return Response({
#                     'message': 'Login successful',
#                     'token': token.key,
#                     'bank_id': bank.id,
#                     'bank_name': bank.name,
#                     'api_key': bank.api_key,
#                       'iso_profile': {
#                         'id': bank.iso_profile.id if bank.iso_profile else None,
#                         'name': bank.iso_profile.name if bank.iso_profile else None,
#                         'message_type': bank.iso_profile.message_type if bank.iso_profile else None
#                     }

#                 }, status=status.HTTP_200_OK)
                
#             except Bank.DoesNotExist:
#                 return Response({
#                     'message': 'Bank account not found'
#                 }, status=status.HTTP_404_NOT_FOUND)
#         else:
#             return Response({
#                 'message': 'Invalid email or password'
#             }, status=status.HTTP_401_UNAUTHORIZED)
    
#     return Response({
#         'message': 'Invalid input',
#         'errors': serializer.errors
#     }, status=status.HTTP_400_BAD_REQUEST)

@api_view(["POST"])
@permission_classes([AllowAny])
def login_bank_api(request):
    """
    Bank login endpoint
    """
    serializer = BankLoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    email = serializer.validated_data["email"]
    password = serializer.validated_data["password"]

    # Authenticate user
    user = authenticate(request, username=email, password=password)

    if not user:
        return Response(
            {"detail": "Invalid credentials"},
            status=status.HTTP_401_UNAUTHORIZED
        )

    # Fetch bank WITH iso_profile
    try:
        bank = (
            Bank.objects
            .select_related("iso_profile")
            .get(user=user)
        )
    except Bank.DoesNotExist:
        return Response(
            {"detail": "No active bank profile linked to this user"},
            status=status.HTTP_403_FORBIDDEN
        )

    # Create or fetch token
    token, _ = Token.objects.get_or_create(user=user)

    return Response(
        {
            "token": token.key,
            "bank": BankSerializer(bank).data
        },
        status=status.HTTP_200_OK
    )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_bank_details_api(request):
    """
    GET /api/auth/me/
    Get current authenticated bank details
    """
    try:
        bank = Bank.objects.get(user=request.user)
        serializer = BankDetailSerializer(bank)
        
        return Response({
            'message': 'Bank details retrieved successfully',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Bank.DoesNotExist:
        return Response({
            'message': 'Bank account not found for this user'
        }, status=status.HTTP_404_NOT_FOUND)



# reconciliation/views.py

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_reconciliation_api(request):
    """
    POST /api/reconcile/upload/
    Upload and process ISO 20022 XML file + store in cloud
    """
    data=request.data

    print(f"Request data: {data}")


    serializer = UploadFileOnlySerializer(data=request.data)
    print(data, "uplaoding")
    # serializer = UploadFileOnlySerializer(data=request.data,files=request.FILES)
    
    if not serializer.is_valid():
        print("serializer not")
        return Response({
            'message': 'Invalid file upload',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get bank from authenticated user
    try:
        bank = Bank.objects.get(user=request.user)

        iso_profile = bank.iso_profile
        if not iso_profile:
            return Response({
                'message': 'No ISO profile configured for this bank'
            }, status=status.HTTP_400_BAD_REQUEST)

    except Bank.DoesNotExist:
        return Response({
            'message': 'Bank not found for authenticated user'
        }, status=status.HTTP_404_NOT_FOUND)
    
    uploaded_file = serializer.validated_data['file_name']
    
    try:
        # Start timing
        start_time = time.time()
        
        # Read XML content
        xml_content = uploaded_file.read().decode('utf-8')
        xml_bytes = xml_content.encode('utf-8')
        
        # DEBUG: Print first 500 chars for troubleshooting
        print(f"[DEBUG] Parsing file: {uploaded_file.name}")
        print(f"[DEBUG] First 500 chars:\n{xml_content[:500]}")
        
        # Parse and validate based on file type
        file_extension = uploaded_file.name.lower().split('.')[-1]
        
        if file_extension == 'xml':
            # total_transactions, mismatches_count, mismatch_details = parse_iso20022_xml(xml_content)
            total_transactions, mismatches_count, mismatch_details = parse_iso20022_xml(
                    xml_content=xml_content,
                    iso_profile=iso_profile
                )

        else:
            # For other formats, use the generic parser
            total_transactions, mismatches_count, mismatch_details = parse_iso20022_file(
                xml_bytes,
                uploaded_file.name
            )
        
        print(f"[DEBUG] Parsed: {total_transactions} transactions, {mismatches_count} mismatches")
        
        # Generate XRPL hash for audit trail
        xrpl_hash = generate_xrpl_hash(xml_content)
        
        # Format results
        result_json = format_reconciliation_result(
            total_transactions,
            mismatches_count,
            mismatch_details
        )
        
        # Calculate processing time
        processing_time = int((time.time() - start_time) * 1000)
        
        # Upload to cloud storage
        file_url, file_hash, file_size = upload_to_cloud_storage(
            xml_bytes,
            uploaded_file.name,
            bank.id
        )
        
        # Create reconciliation log
        recon_log = ISOReconciliationLog.objects.create(
            bank=bank,
            iso_profile=iso_profile,
            filename=uploaded_file.name,
            total_transactions=total_transactions,
            mismatches=mismatches_count,
            xrpl_hash=xrpl_hash,
            raw_xml=xml_content,
            result_json=result_json,
            processing_time_ms=processing_time
        )

        # recon_log = ISOReconciliationLog.objects.create(
        #     bank=bank,
        #     filename=uploaded_file.name,
        #     total_transactions=total_transactions,
        #     mismatches=mismatches_count,
        #     xrpl_hash=xrpl_hash,
        #     raw_xml=xml_content,
        #     result_json=result_json,
        #     processing_time_ms=processing_time
        # )

        # Create document record
        iso_document = ISODocument.objects.create(
            bank=bank,
            file_name=uploaded_file.name,
            file_url=file_url,
            file_size_bytes=file_size,
            file_hash=file_hash,
            log=recon_log
        )
        
        # Serialize response
        response_serializer = ISOReconciliationDetailSerializer(recon_log)
        # document_serializer = UploadFileOnlySerializer(iso_document)
        document_serializer = ISODocumentSerializer(iso_document)

        
        return Response({
            'message': 'Reconciliation completed successfully',
            'reconciliation': response_serializer.data,
            'document': document_serializer.data
        }, status=status.HTTP_201_CREATED)
    
    except ValueError as e:
        # XML parsing or validation error
        print(f"[ERROR] Validation failed: {str(e)}")
        return Response({
            'message': 'File validation failed',
            'error': str(e),
            'file_name': uploaded_file.name
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        # Unexpected error
        import traceback
        print(f"[ERROR] Unexpected error: {str(e)}")
        print(traceback.format_exc())
        
        return Response({
            'message': 'Reconciliation failed',
            'error': str(e),
            'error_type': type(e).__name__
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_reconciliations_api(request):
    """
    GET /api/reconcile/list/
    List all reconciliations for authenticated bank
    Query params: limit, offset (pagination)
    """
    try:
        bank = Bank.objects.get(user=request.user)
    except Bank.DoesNotExist:
        return Response({
            'message': 'Bank not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Get query parameters
    limit = int(request.GET.get('limit', 10))
    offset = int(request.GET.get('offset', 0))
    
    # Query reconciliations
    reconciliations = ISOReconciliationLog.objects.filter(
        bank=bank
    )[offset:offset+limit]
    
    total_count = ISOReconciliationLog.objects.filter(bank=bank).count()
    
    serializer = ISOReconciliationListSerializer(reconciliations, many=True)
    
    return Response({
        'message': 'Reconciliations retrieved successfully',
        'data': serializer.data,
        'pagination': {
            'total': total_count,
            'limit': limit,
            'offset': offset,
            'has_more': (offset + limit) < total_count
        }
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_reconciliation_detail_api(request, log_id):
    """
    GET /api/reconcile/<log_id>/
    Get detailed reconciliation information
    """
    try:
        bank = Bank.objects.get(user=request.user)
        recon_log = ISOReconciliationLog.objects.get(id=log_id, bank=bank)
        
        serializer = ISOReconciliationDetailSerializer(recon_log)
        
        return Response({
            'message': 'Reconciliation details retrieved',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    except Bank.DoesNotExist:
        return Response({
            'message': 'Bank not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except ISOReconciliationLog.DoesNotExist:
        return Response({
            'message': 'Reconciliation log not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_reconciliation_stats_api(request):
    """
    GET /api/reconcile/stats/
    Get dashboard statistics for authenticated bank
    """
    try:
        bank = Bank.objects.get(user=request.user)
    except Bank.DoesNotExist:
        return Response({
            'message': 'Bank not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Calculate stats
    all_recons = ISOReconciliationLog.objects.filter(bank=bank)
    
    total_reconciliations = all_recons.count()
    total_transactions = all_recons.aggregate(Sum('total_transactions'))['total_transactions__sum'] or 0
    total_mismatches = all_recons.aggregate(Sum('mismatches'))['mismatches__sum'] or 0
    
    # Calculate average accuracy
    if total_transactions > 0:
        average_accuracy = ((total_transactions - total_mismatches) / total_transactions) * 100
    else:
        average_accuracy = 0
    
    # Files processed today
    today = timezone.now().date()
    files_today = all_recons.filter(
        uploaded_at__date=today
    ).count()
    
    stats_data = {
        'total_reconciliations': total_reconciliations,
        'total_transactions_processed': total_transactions,
        'total_mismatches': total_mismatches,
        'average_accuracy': round(average_accuracy, 2),
        'files_processed_today': files_today
    }
    
    serializer = GetISOReconciliationStatsSerializer(stats_data)
    
    return Response({
        'message': 'Statistics retrieved successfully',
        'data': serializer.data
    }, status=status.HTTP_200_OK)

 

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_documents_api(request):
    """
    GET /api/reconcile/documents/
    List all uploaded ISO documents for authenticated bank
    """
    try:
        bank = Bank.objects.get(user=request.user)
    except Bank.DoesNotExist:
        return Response({
            'message': 'Bank not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Get query parameters
    limit = int(request.GET.get('limit', 10))
    offset = int(request.GET.get('offset', 0))
    
    # Query documents
    documents = ISODocument.objects.filter(
        bank=bank
    ).select_related('log')[offset:offset+limit]
    
    total_count = ISODocument.objects.filter(bank=bank).count()
    
    serializer = GetISODocumentListSerializer(documents, many=True)
    
    return Response({
        'message': 'Documents retrieved successfully',
        'data': serializer.data,
        'pagination': {
            'total': total_count,
            'limit': limit,
            'offset': offset,
            'has_more': (offset + limit) < total_count
        }
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_document_detail_api(request, document_id):
    """
    GET /api/reconcile/documents/<document_id>/
    Get document details including download URL
    """
    try:
        bank = Bank.objects.get(user=request.user)
        document = ISODocument.objects.get(id=document_id, bank=bank)
        
        serializer = ISODocumentSerializer(document)
        
        return Response({
            'message': 'Document details retrieved',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    except Bank.DoesNotExist:
        return Response({
            'message': 'Bank not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except ISODocument.DoesNotExist:
        return Response({
            'message': 'Document not found'
        }, status=status.HTTP_404_NOT_FOUND)
