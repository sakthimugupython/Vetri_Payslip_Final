from django.contrib import admin
from .models import Payslip

@admin.register(Payslip)
class PayslipAdmin(admin.ModelAdmin):
    list_display = ['employee_name', 'employee_id', 'pay_period', 'net_payable', 'created_at']
    list_filter = ['created_at', 'payment_date']
    search_fields = ['employee_name', 'employee_id']
    readonly_fields = ['created_at']
