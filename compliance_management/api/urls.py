from django.urls import path
from . import views
from compliance_management.api.views import list_reconciliations_api



urlpatterns = [
    path('login_api/', views.login_api, name="login_api"),
    path('register_bank_api/', views.register_bank_api, name="register_bank_api"),
    path('login_bank_api/', views.login_bank_api, name="login_bank_api"),
    path('get_bank_details_api/', views.get_bank_details_api, name="get_bank_details_api"),
    path('upload_reconciliation_api/', views.upload_reconciliation_api, name="upload_reconciliation_api"),
    # path('list_reconciliations_api/', views.list_reconciliations_api, name="list_reconciliations_api"),
    path('list_reconciliations_api/', list_reconciliations_api, name='list_reconciliations_api'),

    path('get_reconciliation_detail_api/<int:log_id>/', views.get_reconciliation_detail_api, name="get_reconciliation_detail_api"),
    path('get_reconciliation_stats_api/', views.get_reconciliation_stats_api, name='get_reconciliation_stats_api'),
    path('list_documents_api/', views.list_documents_api, name='list_documents_api'),
    path('list_documents_api/', views.list_documents_api, name='list_documents_api'),
    path('get_document_detail_api/<int:document_id>/', views.get_document_detail_api, name="get_document_detail_api"),
    # path('delete_document_api/<int:document_id>/', views.delete_document_api, name="delete_document_api"),
    
]
