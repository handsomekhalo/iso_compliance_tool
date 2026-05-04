from django.urls import path
from . import views


urlpatterns = [
    path('send_payment_api/', views.send_payment_api, name='send_payment_api'),
    
]
