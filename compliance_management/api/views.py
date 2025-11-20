import json
import random
from datetime import datetime

from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status


import datetime
from datetime import datetime
import json
import random
from requests import Response

from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from rest_framework.response import Response
from rest_framework import status


from rest_framework.decorators import api_view, permission_classes

from rest_framework import (
    status,
    permissions,
    authentication
)

from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes
)




from .serializers import UserModelSerializer


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
