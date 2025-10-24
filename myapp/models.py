from django.db import models
from django.contrib.auth.models import User

class Payslip(models.Model):
    employee_name = models.CharField(max_length=100)
    employee_id = models.CharField(max_length=50)
    pay_period = models.CharField(max_length=100)
    paid_days = models.IntegerField()
    loss_of_pay_days = models.IntegerField()
    payment_date = models.DateField()
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2)
    incentive = models.DecimalField(max_digits=10, decimal_places=2)
    gross_earnings = models.DecimalField(max_digits=10, decimal_places=2)
    income_tax = models.DecimalField(max_digits=10, decimal_places=2)
    total_deduction = models.DecimalField(max_digits=10, decimal_places=2)
    net_payable = models.DecimalField(max_digits=10, decimal_places=2)
    amount_in_words = models.TextField()
    pdf_file = models.FileField(upload_to='payslips/')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.employee_name} - {self.employee_id} - {self.pay_period}"
