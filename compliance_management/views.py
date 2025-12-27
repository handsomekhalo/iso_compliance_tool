from django.shortcuts import render

# Create your views here.
from django.conf import settings # Ensure this import is at the top

import json
import secrets
import string
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.middleware.csrf import get_token
import requests
from rest_framework.authtoken.models import Token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.urls import reverse, reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from compliance_management import constants
from compliance_management.api.serializers import ISOReconciliationListSerializer
from compliance_management.decorators import session_timeout
from compliance_management.general_func_classes import _send_email_thread, api_connection, host_url
from compliance_management.models import User
from django.http import JsonResponse
import json # You're using json.dumps, so ensure this is imported
from django.shortcuts import redirect
from django.contrib.sessions.models import Session
import json
import requests
from rest_framework import status # Import DRF status codes for clarity
# from . import constants # Ensure constants module is correctly imported for JSON_APPLICATION
import logging

from compliance_management.storage_util import open_iso_xml_in_backblaze, upload_iso_xml_to_backblaze

logger = logging.getLogger(__name__)
import threading
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from .decorators import session_timeout, check_token_in_session
from .models import Bank, ISOReconciliationLog, User
from django.urls import reverse, NoReverseMatch

# from .utils import host_url, api_connection, generate_password, _send_email_thread


@ensure_csrf_cookie
def csrf(request):
    """
    Sets the CSRF cookie and returns the token
    """
    token = get_token(request)

    print(f"CSRF token set: {token}")  # Debugging line
    return JsonResponse({'csrfToken': token})


def get_data_on_success(response_data):
    status = response_data.get('status')
    if status == 'success':
        data = response_data.get('data')
    else:
        data = []
    return data


def generate_password(length=12, include_digits=True, include_special_chars=True):
    letters = string.ascii_letters
    digits = string.digits if include_digits else ''
    special_chars = string.punctuation if include_special_chars else ''

    characters = letters + digits + special_chars

    length = max(length, 8)

    password = ''.join(secrets.choice(characters) for _ in range(length))

    return password



def set_csrf_token(request):
     response = JsonResponse({'detail': 'CSRF cookie set'})
     response.set_cookie('csrftoken', get_token(request)) 
     return response



# View that redirects to Next.js
def login_view(request):
    return redirect("http://localhost:3000/")  # Next.js is running here
    # return redirect('http://52.14.111.23:3000/')  # or your real domain



@ensure_csrf_cookie  # This ensures the CSRF cookie is set
def login(request):
    """User login function with API."""
    if request.method != "POST":
        return JsonResponse({
            'status': 'error', 
            'message': 'Only POST requests are allowed'
        }, status=405)

    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
        # remember_me = data.get('rememberMe', False)

        if not email or not password:
            return JsonResponse({
                'status': 'error',
                'message': 'Email and password are required'
            }, status=400)

        # Get the existing token if any
        token = request.session.get('token')
        
        headers = {
            'Content-Type': 'application/json',
            "Authorization": f"Token {token}" if token else ""
        }

        payload = json.dumps({
            'email': email,
            'password': password,
            # 'remember_me': remember_me
        })

        url = f"{host_url(request)}{reverse_lazy('login_api')}"
        
        try:
            response_data = requests.post(
                url, 
                headers=headers, 
                data=payload, 
                timeout=10
            )
            
            if response_data.status_code == 200:
                response_json = response_data.json()
                
                # Store token in session if remember_me is True
                # if remember_me and 'token' in response_json:
                #     request.session['token'] = response_json['token']
                
                return JsonResponse({
                    'status': 'success', 
                    'data': response_json
                })
            
            
            return JsonResponse({
                'status': 'error',
                'message': response_data.json().get('message', 'Login failed'),
            }, status=response_data.status_code)

        except requests.exceptions.RequestException as e:
            return JsonResponse({
                'status': 'error',
                'message': f'API request failed: {str(e)}'
            }, status=500)

    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error', 
            'message': 'Invalid JSON data'
        }, status=400)




@csrf_exempt
def upload_reconciliation(request):
    if request.method != "POST":
        return JsonResponse({'status': 'error', 'message': 'Only POST requests are allowed'}, status=405)

    try:
        # Extract token from header or session
        auth_header = request.headers.get("Authorization", "")
        token = None

        if auth_header.startswith("Token "):
            token = auth_header.split("Token ")[-1]
        elif auth_header.startswith("Bearer "):
            token = auth_header.split("Bearer ")[-1]

        if not token:
            token = request.session.get('token')

        if not token:
            return JsonResponse({'status': 'error', 'message': 'Authentication required'}, status=401)

        # ✅ Get user from token
        try:
            user = Token.objects.select_related("user").get(key=token).user
            bank = Bank.objects.get(user=user)
        except Token.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Invalid token'}, status=401)
        except Bank.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Bank not found'}, status=404)

        # Get uploaded file
        uploaded_file = request.FILES.get('file_name')
        if not uploaded_file:
            return JsonResponse({'status': 'error', 'message': 'No file uploaded'}, status=400)

        # Prepare headers for API call
        headers = {"Authorization": f"Token {token}"}
        file_name= {'file_name': (uploaded_file.name, uploaded_file.read(), uploaded_file.content_type)}

        # ✅ Include bank_id in API call if needed
        data = {'bank_id': bank.id}

        url = f"{host_url(request)}{reverse_lazy('upload_reconciliation_api')}"
        response_data = requests.post(url, headers=headers, files=file_name, data=data, timeout=30)

        if response_data.status_code in [200, 201]:
            return JsonResponse({'status': 'success', 'data': response_data.json()})

        error_message = response_data.json().get('message', 'Upload failed')
        return JsonResponse({'status': 'error', 'message': error_message}, status=response_data.status_code)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Unexpected error: {str(e)}'}, status=500)

# @csrf_exempt
# def upload_reconciliation(request):
#     if request.method != "POST":
#         return JsonResponse({'status': 'error', 'message': 'Only POST requests are allowed'}, status=405)

#     try:
#         # ✅ Check header first
#         auth_header = request.headers.get("Authorization", "")
#         token = None

#         if auth_header.startswith("Token "):
#             token = auth_header.split("Token ")[-1]
#         elif auth_header.startswith("Bearer "):
#             token = auth_header.split("Bearer ")[-1]

#         # ✅ Fallback to session
#         if not token:
#             token = request.session.get('token')

#         print("Upload reconciliation called. Token:", token)

#         if not token:
#             return JsonResponse({'status': 'error', 'message': 'Authentication required. Please login first.'}, status=401)

#         # Get uploaded file
#         uploaded_file = request.FILES.get('file')
#         if not uploaded_file:
#             return JsonResponse({'status': 'error', 'message': 'No file uploaded'}, status=400)

#         # Prepare headers for API call
#         headers = {"Authorization": f"Token {token}"}
#         files = {'file': (uploaded_file.name, uploaded_file.read(), uploaded_file.content_type)}

#         url = f"{host_url(request)}{reverse_lazy('upload_reconciliation_api')}"
#         response_data = requests.post(url, headers=headers, files=files, timeout=30)

#         if response_data.status_code in [200, 201]:
#             return JsonResponse({'status': 'success', 'data': response_data.json()})

#         error_message = response_data.json().get('message', 'Upload failed')
#         return JsonResponse({'status': 'error', 'message': error_message}, status=response_data.status_code)

#     except Exception as e:
#         return JsonResponse({'status': 'error', 'message': f'Unexpected error: {str(e)}'}, status=500)

    

    
@csrf_exempt
def list_reconciliations(request):
    """
    Proxy view to retrieve reconciliation logs for the authenticated bank.
    Retrieves DRF reconciliation endpoint results and applies presigned URLs.
    """
    if request.method != "GET":
        return JsonResponse({
            "status": "error",
            "message": "Method not allowed"
        }, status=405)

    try:
        # 1. Extract token
        auth_header = request.headers.get("Authorization", "")
        token = None

        if auth_header.startswith("Token "):
            token = auth_header.split("Token ")[-1]
        elif auth_header.startswith("Bearer "):
            token = auth_header.split("Bearer ")[-1]

        if not token:
            return JsonResponse({
                "status": "error",
                "message": "Authorization token is required."
            }, status=401)

        # 2. Get the user from the token
        try:
            user = Token.objects.select_related("user").get(key=token).user
        except Token.DoesNotExist:
            return JsonResponse({
                "status": "error",
                "message": "Invalid or expired token."
            }, status=401)

        # Query params for pagination
        limit = request.GET.get("limit", 10)
        offset = request.GET.get("offset", 0)

        # 3. Prepare API call
        headers = {
            "Authorization": f"Token {token}",
            "Content-Type": "application/json"
        }

        # 4. Build URL for reconciliation API
        url_path = reverse('list_reconciliations_api')
        # reconciliation_url = f"{host_url(request)}{url_path}?limit={limit}&offset={offset}"
        reconciliation_url = f"{host_url(request)}{url_path}"


        # 5. Call DRF reconciliation API
        response = requests.get(reconciliation_url, headers=headers, timeout=10)
        
        # DEBUG: Print response details BEFORE raise_for_status
     
        
        # Check if response is successful
        if response.status_code != 200:
            return JsonResponse({
                "status": "error",
                "message": f"API returned {response.status_code}: {response.text}"
            }, status=response.status_code)

        response_data = response.json()
        
        if "data" not in response_data:
            print('❌ Invalid response data:', response_data)
            return JsonResponse({
                "status": "error",
                "message": "Invalid reconciliation API response"
            }, status=500)

        reconciliations = response_data["data"]

        
        # 6. Apply presigned URLs
        for rec in reconciliations:
            if 'uploaded_file' in rec and rec['file_url']:
                rec['uploaded_file'] = open_iso_xml_in_backblaze(rec['file_url'])

            if 'processed_file' in rec and rec['processed_file']:
                rec['processed_file'] = open_iso_xml_in_backblaze(rec['processed_file'])

        # 7. Final Response
        return JsonResponse({
            "status": "success",
            "data": reconciliations,
            "pagination": response_data.get("pagination", {}),
            "message": "Reconciliation logs retrieved successfully."
        }, status=200)

    except requests.exceptions.RequestException as e:
        print('❌ Request Exception:', str(e))
        import traceback
        traceback.print_exc()
        return JsonResponse({
            "status": "error",
            "message": f"Request failed: {str(e)}"
        }, status=500)

    except Exception as e:
        print('❌ General Exception:', str(e))
        import traceback
        traceback.print_exc()
        return JsonResponse({
            "status": "error",
            "message": f"Server error: {str(e)}"
        }, status=500)

