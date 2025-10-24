from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('generate-payslip/', views.generate_payslip, name='generate_payslip'),
    path('payslip-preview/', views.payslip_preview, name='payslip_preview'),
    path('generate-pdf-download/', views.generate_pdf_download, name='generate_pdf_download'),
    path('save-payslip-to-database/', views.save_payslip_to_database, name='save_payslip_to_database'),
    path('view-payslips/', views.view_payslips, name='view_payslips'),
    path('check-existing-payslip/', views.check_existing_payslip, name='check_existing_payslip'),
    path('payslip/<int:payslip_id>/', views.payslip_detail, name='payslip_detail'),
    path('delete-payslip/<int:payslip_id>/', views.delete_payslip, name='delete_payslip'),
]
