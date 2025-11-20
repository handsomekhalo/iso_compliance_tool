"""
This module contains the check_token_in_session decorator for views.
"""
from django.shortcuts import redirect
from datetime import datetime
from compliance_management.models import User
from rest_framework.authtoken.models import Token



def check_token_in_session(view_func):
    """
    Decorator for views that checks if the user is logged in.
    """
    def wrapper_view(request, *args, **kwargs):
        token = request.session.get('token')

        if token:
            try:
                response = view_func(request, *args, **kwargs)
                return response
            except Exception as e:
                print('Error in view function:', str(e))
                raise
        else:
            return redirect('login_view')
    return wrapper_view


def otp_required(view_func):

    def wrapped_view(request, *args, **kwargs):

        valid_otp = request.session.get("pin")

        if not valid_otp:
            return redirect('login_view')

        response = view_func(request, *args, **kwargs)

        if response is None:
            return redirect('login_view')

        return response

    return wrapped_view


def session_timeout(view_func):
    """
    Decorator to manage user session activity based on inactivity.

    This decorator checks if the user is authenticated. If authenticated, it checks the
    last activity time stored in the session. If the last activity was more than the specified
    number of minutes (default 30 minutes) ago, the user session is invalidated, and a response
    indicating session timeout is returned. Otherwise, it updates the last activity time to
    the current time.

    Args:
        minutes (int): The number of minutes of inactivity after which the session expires.
    
    Returns:
        function: The wrapped view function.
    """

    def wrapped_view(request, *args, **kwargs):
        user = request.session.get('user_id')
        if user:
            now = datetime.now()
            last_activity = request.session.get('last_activity')
            if last_activity:
                last_activity_time = datetime.strptime(last_activity, '%Y-%m-%d %H:%M:%S.%f')
                if (now - last_activity_time).seconds > 30*60:
                    # Invalidate the session
                    request.session.flush()
                    return redirect('login_view')
            request.session['last_activity'] = now.strftime('%Y-%m-%d %H:%M:%S.%f')
        return view_func(request, *args, **kwargs)
    return wrapped_view

# def admin_required(view_func):
#     """
#     Decorator to ensure that the user accessing the view has admin privileges.

#     This decorator checks the user's token from the session, verifies the user's role,
#     and allows access only to users with roles 'ADMIN' or 'COMMUNITY_ADVISORY_OFFICER'.
#     If the user does not have the required role, they are redirected to the login view.

#     Args:
#         view_func (function): The view function to be decorated.

#     Returns:
#         function: The wrapped view function with the admin role check.
#     """
#     def wrapped_view(request, *args, **kwargs):

#         token = request.session['token']
#         user_token = Token.objects.filter(key=token).values('user_id')

#         if user_token.exists():
#             user_id = user_token[0]['user_id']
#             role_id = User.objects.get(id=user_id).user_type_id
#             # role = UserType.objects.get(id=role_id).name
#             allowed_roles = ['ADMIN', 'COMMUNITY_ADVISORY_OFFICER','']
#             if role not in allowed_roles:
#                 return redirect('login_view')
#         return view_func(request, *args, **kwargs)

#     return wrapped_view
