from django.urls import path
from . import views


urlpatterns = [
    path('send_payment_api/', views.send_payment_api, name='send_payment_api'),
    path('payment_webhook_api/', views.payment_webhook_api, name='payment_webhook_api'),
    path('list_payments_api/', views.list_payments_api, name='list_payments_api'),
    path('payment_detail_api/<int:payment_id>/', views.payment_detail_api, name='payment_detail_api'),
    
]
