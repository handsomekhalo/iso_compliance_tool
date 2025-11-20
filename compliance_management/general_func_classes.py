"""
General functions and classes are stored here to remove duplicated accross the system.
"""

import json
from django.conf import settings
import requests
from rest_framework import serializers


class BaseFormSerializer(serializers.Serializer):
    """Base form serializer for cleaning incoming and outgoing data"""

    def create(self, validated_data):
        """Override create method to do nothing"""

    def update(self, instance, validated_data):
        """Override create method to do nothing"""


# def host_url(request):
#     """
#     This function is used to get the base url of the application.
#     """
#     protocol = request.scheme
#     host = request.get_host()
#     base_url = f"{protocol}://{host}"
#     return base_url

# def host_url(request):
#     scheme = "https" if settings.USE_HTTPS else "http"
#     host = request.get_host()
#     return f"{scheme}://{host}"
def host_url(request):
    if hasattr(settings, "USE_HTTPS"):
        scheme = "https" if settings.USE_HTTPS else "http"
    else:
        scheme = "https" if request.is_secure() else "http"

    host = request.get_host()
    return f"{scheme}://{host}"


# def api_connection(method, url, headers, data):
#     """This function is used to connect to the api."""
#     response = requests.request(method, url, headers=headers, data=data, timeout=120)
#     # response_data = json.loads(response.json())
#     response_data = response.json()

#     return response_data


def api_connection(method, url, headers, data=None):
    """
    Connects to an external API and handles JSON data.
    
    Args:
        method (str): The HTTP method (e.g., 'GET', 'POST').
        url (str): The URL of the API endpoint.
        headers (dict): The request headers.
        data (dict, optional): The JSON data to send. Defaults to None.

    Returns:
        dict or list: The JSON response data, or a dictionary with an error message.
    """
    try:
        if data:
            response = requests.request(method, url, headers=headers, json=data, timeout=120)
        else:
            response = requests.request(method, url, headers=headers, timeout=120)

        response.raise_for_status()  # This will raise an HTTPError for bad responses (4xx or 5xx)

        return response.json()

    except requests.exceptions.RequestException as e:
        # Catch network-related errors and HTTP errors
        print(f"Network or HTTP error during API call: {e}")
        return {"status": "error", "message": f"Network or HTTP error: {str(e)}"}
    except json.JSONDecodeError:
        # Catch cases where the response is not valid JSON
        print(f"Error decoding JSON response from API: {response.text}")
        return {"status": "error", "message": "Invalid JSON response from API."}



def _send_email_thread(url, headers, payload):
    """This function is used to send email in a thread."""
    requests.post(url=url, headers=headers, data=payload, timeout=120)
