from django.urls import path

from compliance_management.export_view import export_reconciliation_api
from . import views
from compliance_management.api.views import iso_field_rule_detail_api, iso_field_rules_api, list_reconciliations_api



urlpatterns = [
    path('login_api/', views.login_api, name="login_api"),
    path('register_bank_api/', views.register_bank_api, name="register_bank_api"),
    # path('login_bank_api/', views.login_bank_api, name="login_bank_api"),
    path('get_bank_details_api/', views.get_bank_details_api, name="get_bank_details_api"),
    path('upload_reconciliation_api/', views.upload_reconciliation_api, name="upload_reconciliation_api"),
    # path('list_reconciliations_api/', views.list_reconciliations_api, name="list_reconciliations_api"),
    path('list_reconciliations_api/', list_reconciliations_api, name='list_reconciliations_api'),
    path('get_reconciliation_detail_api/<int:log_id>/', views.get_reconciliation_detail_api, name="get_reconciliation_detail_api"),
    path('get_reconciliation_stats_api/', views.get_reconciliation_stats_api, name='get_reconciliation_stats_api'),
    path('list_documents_api/', views.list_documents_api, name='list_documents_api'),
    path('get_document_detail_api/<int:document_id>/', views.get_document_detail_api, name="get_document_detail_api"),
    path('get_my_role_api/',views.get_my_role_api,      name='get_my_role_api'),
    path('list_bank_users_api/',views.list_bank_users_api,  name='list_bank_users_api'),
    path('invite_user_api/',views.invite_user_api,name='invite_user_api'),
    path('update_user_role_api/<int:user_id>/',views.update_user_role_api, name='update_user_role_api'),
    path('remove_user_api/<int:user_id>/',            views.remove_user_api,      name='remove_user_api'),
    path("reconcile/<int:log_id>/export/", export_reconciliation_api, name="reconcile-export"),
    path('activate_user_api/<int:user_id>/', views.activate_user_api, name='activate_user_api'),
    path('iso_field_rule_detail_api/<int:profile_id>/<int:rule_id>/', iso_field_rule_detail_api, name='iso_field_rule_detail_api'),
    path('iso_field_rules_api/<int:profile_id>/', iso_field_rules_api, name='iso_field_rules_api'),
    # path('delete_document_api/<int:document_id>/', views.delete_document_api, name="delete_document_api"),
    
]
