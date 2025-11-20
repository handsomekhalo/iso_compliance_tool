from django.urls import path
import compliance_management.api.views as views



urlpatterns = [
    path('login_api/', views.login_api, name="login_api"),
]
