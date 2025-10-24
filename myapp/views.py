from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.conf import settings
from django.db.models import Q
from .models import Payslip
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import os
from datetime import datetime
from decimal import Decimal


from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

# Register DejaVu Sans font for Unicode support including rupee symbol
try:
    font_path = os.path.join(settings.BASE_DIR, 'myapp', 'static', 'fonts', 'DejaVuSans.ttf')
    bold_font_path = os.path.join(settings.BASE_DIR, 'myapp', 'static', 'fonts', 'DejaVuSans-Bold.ttf')
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))
        if os.path.exists(bold_font_path):
            pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', bold_font_path))
            FONT_NAME = 'DejaVuSans-Bold'
        else:
            FONT_NAME = 'DejaVuSans'
    else:
        # Fallback to Helvetica if DejaVu not available
        FONT_NAME = 'Helvetica-Bold'
except:
    # Ultimate fallback
    FONT_NAME = 'Helvetica-Bold'

def generate_payslip_pdf(filepath, context):
    """Generate PDF payslip using ReportLab - matching HTML preview design"""

    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=10,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
        encoding='utf-8'
    )
    elements = []
    styles = getSampleStyleSheet()

    # Custom styles matching HTML preview
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#5b4d9e'),
        spaceAfter=10,
        alignment=TA_LEFT
    )

    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=5
    )

    # Two-column header: Company info (left) + Employee Statement (right)
    logo_path = os.path.join(settings.BASE_DIR, 'myapp', 'static', 'images', 'VIS LOGO.png')

    # Left column - Logo + Company info
    company_info = []
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=70, height=70)
        logo.hAlign = 'LEFT'
        company_info.append(logo)
        company_info.append(Spacer(1, 6))

    company_info.append(Paragraph('<b>VETRI IT SYSTEMS PVT LTD.,</b>', title_style))
    company_info.append(Paragraph('Shanthi complex, Second floor,', normal_style))
    company_info.append(Paragraph('Surandai, Tenkasi - 627 859', normal_style))
    company_info.append(Paragraph('India', normal_style))

    # Right column - Employee Statement
    employee_info = []
    employee_info.append(Spacer(1, 15))
    employee_info.append(Paragraph('<b>Employee Statement</b>', title_style))

    employee_text = f"""
    <b>Employee Name:</b> {context['employee_name']}<br/>
    <b>Employee ID:</b> {context['employee_id']}<br/>
    <b>Pay Period:</b> {context['pay_period']}<br/>
    <b>Paid Days:</b> {context['paid_days']}<br/>
    <b>Loss of Pay Days:</b> {context['loss_of_pay_days']}<br/>
    <b>Payment Date:</b> {context['payment_date']}
    """

    employee_info.append(Paragraph(employee_text, ParagraphStyle(
        'EmployeeDetails',
        parent=styles['Normal'],
        fontSize=10,
        leading=20,
        spaceAfter=5,
    )))

    # Combine into two-column table
    header_table = Table(
        [[company_info, employee_info]],
        colWidths=[250, 250]
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))

    elements.append(header_table)
    elements.append(Spacer(1, 25))

    # Earnings and Deductions tables (side-by-side with improved design)
    # Use rupee symbol with proper encoding
    rupee = '\u20B9'
    earnings_data = [
        ['Earnings', 'Amount'],
        ['Basic', f'{rupee} {context["basic_salary"]}'],
        ['Incentive', f'{rupee} {context["incentive"]}'],
        ['Gross Earnings', f'{rupee} {context["gross_earnings"]}']
    ]

    deductions_data = [
        ['Deduction', 'Amount'],
        ['Income Tax', f'{rupee} {context["income_tax"]}'],
        ['', ''],
        ['Total Deduction', f'{rupee} {context["total_deduction"]}']
    ]

    earnings_table = Table(earnings_data, colWidths=[140, 100])
    earnings_table.setStyle(TableStyle([
        # Header row styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8f5e9')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('FONTNAME', (0, 0), (-1, 0), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        
        # Body rows styling - use FONT_NAME for rupee symbol support
        ('BACKGROUND', (0, 1), (-1, 2), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, 2), colors.black),
        ('FONTNAME', (0, 1), (-1, 2), FONT_NAME),
        ('FONTSIZE', (0, 1), (-1, 2), 9),
        ('ALIGN', (0, 1), (0, 2), 'LEFT'),
        ('ALIGN', (1, 1), (1, 2), 'RIGHT'),
        
        # Footer row styling (Gross Earnings)
        ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#5b4d9e')),
        ('TEXTCOLOR', (0, 3), (-1, 3), colors.whitesmoke),
        ('FONTNAME', (0, 3), (-1, 3), FONT_NAME),
        ('FONTSIZE', (0, 3), (-1, 3), 10),
        ('ALIGN', (0, 3), (0, 3), 'LEFT'),
        ('ALIGN', (1, 3), (1, 3), 'RIGHT'),
        
        # Padding
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        
        # Borders
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#d0d0d0')),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#d0d0d0')),
        ('LINEABOVE', (0, 3), (-1, 3), 1, colors.HexColor('#d0d0d0')),
        ('ROUNDEDCORNERS', [8, 8, 8, 8])
    ]))

    deductions_table = Table(deductions_data, colWidths=[140, 100])
    deductions_table.setStyle(TableStyle([
        # Header row styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8f5e9')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('FONTNAME', (0, 0), (-1, 0), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        
        # Body rows styling - use FONT_NAME for rupee symbol support
        ('BACKGROUND', (0, 1), (-1, 2), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, 2), colors.black),
        ('FONTNAME', (0, 1), (-1, 2), FONT_NAME),
        ('FONTSIZE', (0, 1), (-1, 2), 9),
        ('ALIGN', (0, 1), (0, 2), 'LEFT'),
        ('ALIGN', (1, 1), (1, 2), 'RIGHT'),
        
        # Footer row styling (Total Deduction)
        ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#5b4d9e')),
        ('TEXTCOLOR', (0, 3), (-1, 3), colors.whitesmoke),
        ('FONTNAME', (0, 3), (-1, 3), FONT_NAME),
        ('FONTSIZE', (0, 3), (-1, 3), 10),
        ('ALIGN', (0, 3), (0, 3), 'LEFT'),
        ('ALIGN', (1, 3), (1, 3), 'RIGHT'),
        
        # Padding
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        
        # Borders
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#d0d0d0')),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#d0d0d0')),
        ('LINEABOVE', (0, 3), (-1, 3), 1, colors.HexColor('#d0d0d0')),
        ('ROUNDEDCORNERS', [8, 8, 8, 8])
    ]))

    # Place tables side by side with proper spacing
    combined_table = Table([[earnings_table, Spacer(1, 20), deductions_table]], colWidths=[240, 20, 240])
    combined_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(combined_table)
    elements.append(Spacer(1, 30))

    # Net Payable section with new design
    # Create two separate paragraphs for title and subtitle
    title_style = ParagraphStyle(
        'NetPayableTitle',
        parent=styles['Normal'],
        fontSize=13,
        fontName=FONT_NAME,
        textColor=colors.black,
        leading=16,
        fontWeight='BOLD'
    )
    subtitle_style = ParagraphStyle(
        'NetPayableSubtitle',
        parent=styles['Normal'],
        fontSize=9,
        fontName='Helvetica',
        textColor=colors.HexColor('#666666'),
        leading=12
    )
    
    title_para = Paragraph('TOTAL NET PAYABLE', title_style)
    subtitle_para = Paragraph('Gross Earnings - Total Deduction', subtitle_style)
    
    # Combine them in a table-like structure
    left_cell_data = [[title_para], [subtitle_para]]
    left_cell = Table(left_cell_data, colWidths=[200])
    left_cell.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    
    net_payable_data = [
        [left_cell, f'{rupee} {context["net_payable"]}']
    ]
    net_payable_table = Table(net_payable_data, colWidths=[370, 130])  # Adjusted proportions to match design
    net_payable_table.setStyle(TableStyle([
        # Light background for entire section
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9fdf7')),  # Very light green background
        # Purple background only for amount cell
        ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#5b4d9e')),
        ('TEXTCOLOR', (0, 0), (0, 0), colors.black),  # Black text for left cell
        ('TEXTCOLOR', (1, 0), (1, 0), colors.whitesmoke),  # White text for amount
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (1, 0), (1, 0), FONT_NAME),
        ('FONTSIZE', (1, 0), (1, 0), 16),  # Larger font for prominence
        ('TOPPADDING', (0, 0), (-1, -1), 15),   # More padding for height
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15), # More padding for height
        ('LEFTPADDING', (0, 0), (0, 0), 15),    # More left padding
        ('RIGHTPADDING', (1, 0), (1, 0), 20),   # More right padding for blue box
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e0e0d0')),  # Subtle outer border
        ('ROUNDEDCORNERS', [8, 8, 8, 8])  # More rounded corners
    ]))
    elements.append(net_payable_table)
    elements.append(Spacer(1, 10))

    # Amount in words (matching HTML)
    amount_words_style = ParagraphStyle(
        'AmountWords',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_CENTER,
        spaceAfter=15
    )
    elements.append(Paragraph(f'<b>Amount in words:</b> {context["amount_in_words"]}', amount_words_style))
    elements.append(Spacer(1, 20))

    # Signatures section (matching HTML layout)
    elements.append(Paragraph('<b>ACKNOWLEDGED BY,</b>', ParagraphStyle('SignatureTitle', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER, textColor=colors.HexColor('#5b4d9e'), spaceAfter=25)))

    signature_data = [
        ['_' * 25, '_' * 25],
        [context['employee_name'], 'AUTHORISED NAME'],
        [f'Employee, VETRI IT SYSTEMS PVT LTD.', 'Managing Director, VETRI IT SYSTEMS PVT LTD.']
    ]

    signature_table = Table(signature_data, colWidths=[240, 240])
    signature_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, 1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, 1), 9),
        ('FONTSIZE', (0, 2), (-1, 2), 8),
        ('TEXTCOLOR', (0, 2), (-1, 2), colors.HexColor('#5b4d9e')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(signature_table)

    # Add a visible page border using PageTemplate
    from reportlab.platypus import PageTemplate, Frame

    # Create a frame with visible boundary (border)
    main_frame = Frame(
        20, 20,  # x, y position (matching the margins)
        555, 782,  # width, height (A4 minus margins)
        leftPadding=30,
        bottomPadding=30,
        rightPadding=30,
        topPadding=30,
        showBoundary=1,  # This will show the frame boundary as a border!
        id='main_frame'
    )

    # Create page template with the bordered frame
    template = PageTemplate(id='payslip_template', frames=[main_frame])

    # Set the template on the document
    doc.addPageTemplates([template])

    # Build PDF with proper encoding - the frame will provide the border
    doc.build(elements)

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    # Always clear any existing messages for non-authenticated users
    # This prevents old messages from showing on login page
    # Messages are cleared here because logout and other redirects may add messages
    from django.contrib.messages import get_messages
    storage = get_messages(request)
    # Consume all messages to clear them completely
    list(storage)

    # Additional message clearing - clear any remaining messages
    if hasattr(request, 'session'):
        # Clear any session-based messages
        for key in list(request.session.keys()):
            if key.startswith('_messages'):
                del request.session[key]

    if request.method == 'POST':
        username_or_email = request.POST.get('username')
        password = request.POST.get('password')

        # First, try to authenticate with the provided value as username
        user = authenticate(request, username=username_or_email, password=password)

        # If username authentication fails, try to find user by email
        if user is None:
            from django.contrib.auth.models import User
            try:
                # Try to find user by email
                user_obj = User.objects.get(email=username_or_email)
                # Authenticate with the found user's username
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                # No user found with that email
                pass

        if user is not None:
            if user.is_superuser:
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Access denied. Only superusers can login.')
        else:
            messages.error(request, 'Invalid username/email or password.')

    return render(request, 'login.html')

@login_required(login_url='login')
def dashboard_view(request):
    if not request.user.is_superuser:
        logout(request)
        # Don't add error message to prevent it from showing on login page
        return redirect('login')

    return render(request, 'dashboard.html')

def logout_view(request):
    logout(request)
    # Don't add logout message to prevent it from showing on login page
    return redirect('login')

@login_required(login_url='login')
def generate_payslip(request):
    """Show payslip preview page"""
    if request.method == 'POST':
        try:
            # Extract data from POST request
            employee_id = request.POST.get('employee_id')
            pay_period = request.POST.get('pay_period')

            # Check if payslip already exists for this employee and period
            existing_payslip = Payslip.objects.filter(
                employee_id=employee_id,
                pay_period=pay_period
            ).first()

            if existing_payslip:
                return JsonResponse({
                    'success': False,
                    'message': f'Payslip already exists for Employee ID {employee_id} for period {pay_period}. Please check the View Payslips page to access the existing payslip.'
                })

            # Extract data from POST request
            payslip_data = {
                'employee_name': request.POST.get('employee_name'),
                'employee_id': employee_id,
                'pay_period': pay_period,
                'paid_days': int(request.POST.get('paid_days')),
                'loss_of_pay_days': int(request.POST.get('loss_of_pay_days')),
                'payment_date': request.POST.get('payment_date'),
                'basic_salary': Decimal(request.POST.get('basic_salary')),
                'incentive': Decimal(request.POST.get('incentive')),
                'gross_earnings': Decimal(request.POST.get('gross_earnings')),
                'income_tax': Decimal(request.POST.get('income_tax')),
                'total_deduction': Decimal(request.POST.get('total_deduction')),
                'net_payable': Decimal(request.POST.get('net_payable')),
                'amount_in_words': request.POST.get('amount_in_words'),
            }

            # Store data in session for preview page
            request.session['payslip_data'] = {k: str(v) for k, v in payslip_data.items()}

            return JsonResponse({
                'success': True,
                'redirect_url': '/payslip-preview/'
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            }, status=400)

    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)

@login_required(login_url='login')
def check_existing_payslip(request):
    """Check if payslip already exists for employee and period"""
    if request.method == 'POST':
        try:
            employee_id = request.POST.get('employee_id')
            pay_period = request.POST.get('pay_period')

            if not employee_id or not pay_period:
                return JsonResponse({
                    'success': False,
                    'message': 'Employee ID and Pay Period are required'
                })

            existing_payslip = Payslip.objects.filter(
                employee_id=employee_id,
                pay_period=pay_period
            ).first()

            if existing_payslip:
                return JsonResponse({
                    'success': True,
                    'exists': True,
                    'message': f'Payslip already exists for Employee ID {employee_id} for period {pay_period}',
                    'payslip_id': existing_payslip.id
                })
            else:
                return JsonResponse({
                    'success': True,
                    'exists': False,
                    'message': 'No existing payslip found'
                })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error checking payslip: {str(e)}'
            }, status=400)

    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)

@login_required(login_url='login')
def payslip_preview(request):
    """Display payslip preview page"""
    payslip_data = request.session.get('payslip_data')

    if not payslip_data:
        messages.error(request, 'No payslip data found. Please generate a payslip first.')
        return redirect('dashboard')

    return render(request, 'payslip_preview.html', {'payslip_data': payslip_data})

@login_required(login_url='login')
def generate_pdf_download(request):
    """Generate and download PDF from preview page (without saving to database)"""
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)

            # Extract data
            employee_name = data.get('employee_name')
            employee_id = data.get('employee_id')
            pay_period = data.get('pay_period')
            paid_days = int(data.get('paid_days'))
            loss_of_pay_days = int(data.get('loss_of_pay_days'))
            payment_date = data.get('payment_date')
            basic_salary = Decimal(data.get('basic_salary'))
            incentive = Decimal(data.get('incentive'))
            gross_earnings = Decimal(data.get('gross_earnings'))
            income_tax = Decimal(data.get('income_tax'))
            total_deduction = Decimal(data.get('total_deduction'))
            net_payable = Decimal(data.get('net_payable'))
            amount_in_words = data.get('amount_in_words')

            # Prepare context
            context = {
                'employee_name': employee_name,
                'employee_id': employee_id,
                'pay_period': pay_period,
                'paid_days': paid_days,
                'loss_of_pay_days': loss_of_pay_days,
                'payment_date': payment_date,
                'basic_salary': basic_salary,
                'incentive': incentive,
                'gross_earnings': gross_earnings,
                'income_tax': income_tax,
                'total_deduction': total_deduction,
                'net_payable': net_payable,
                'amount_in_words': amount_in_words,
            }

            # Create temporary PDF file
            payslips_dir = os.path.join(settings.MEDIA_ROOT, 'payslips')
            os.makedirs(payslips_dir, exist_ok=True)

            # Generate PDF with unique filename
            temp_filename = f"payslip_{employee_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            filepath = os.path.join(payslips_dir, temp_filename)
            generate_payslip_pdf(filepath, context)

            # Return file for download instead of URL
            from django.http import FileResponse
            response = FileResponse(open(filepath, 'rb'), as_attachment=True)
            response['Content-Disposition'] = f'attachment; filename="{temp_filename}"'

            # Clean up temp file after sending (optional, but good practice)
            import threading
            def cleanup():
                try:
                    os.remove(filepath)
                except:
                    pass
            threading.Timer(5.0, cleanup).start()

            return response

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error generating payslip: {str(e)}'
            }, status=400)

    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)

@login_required(login_url='login')
def save_payslip_to_database(request):
    """Save payslip data to database from preview page"""
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)

            # Extract data
            employee_name = data.get('employee_name')
            employee_id = data.get('employee_id')
            pay_period = data.get('pay_period')
            paid_days = int(data.get('paid_days'))
            loss_of_pay_days = int(data.get('loss_of_pay_days'))
            payment_date = data.get('payment_date')
            basic_salary = Decimal(data.get('basic_salary'))
            incentive = Decimal(data.get('incentive'))
            gross_earnings = Decimal(data.get('gross_earnings'))
            income_tax = Decimal(data.get('income_tax'))
            total_deduction = Decimal(data.get('total_deduction'))
            net_payable = Decimal(data.get('net_payable'))
            amount_in_words = data.get('amount_in_words')

            # Check if payslip already exists
            existing_payslip = Payslip.objects.filter(
                employee_id=employee_id,
                pay_period=pay_period
            ).first()

            if existing_payslip:
                return JsonResponse({
                    'success': False,
                    'message': f'Payslip already exists for Employee ID {employee_id} for period {pay_period}. Please check the View Payslips page.'
                })

            # Prepare context for PDF generation
            context = {
                'employee_name': employee_name,
                'employee_id': employee_id,
                'pay_period': pay_period,
                'paid_days': paid_days,
                'loss_of_pay_days': loss_of_pay_days,
                'payment_date': payment_date,
                'basic_salary': basic_salary,
                'incentive': incentive,
                'gross_earnings': gross_earnings,
                'income_tax': income_tax,
                'total_deduction': total_deduction,
                'net_payable': net_payable,
                'amount_in_words': amount_in_words,
            }

            # Create media directory and generate PDF
            payslips_dir = os.path.join(settings.MEDIA_ROOT, 'payslips')
            os.makedirs(payslips_dir, exist_ok=True)

            filename = f"payslip_{employee_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            filepath = os.path.join(payslips_dir, filename)
            generate_payslip_pdf(filepath, context)

            # Save to database
            payslip = Payslip.objects.create(
                employee_name=employee_name,
                employee_id=employee_id,
                pay_period=pay_period,
                paid_days=paid_days,
                loss_of_pay_days=loss_of_pay_days,
                payment_date=payment_date,
                basic_salary=basic_salary,
                incentive=incentive,
                gross_earnings=gross_earnings,
                income_tax=income_tax,
                total_deduction=total_deduction,
                net_payable=net_payable,
                amount_in_words=amount_in_words,
                pdf_file=f'payslips/{filename}',
                created_by=request.user
            )

            return JsonResponse({
                'success': True,
                'message': 'Payslip saved to records successfully!',
                'payslip_id': payslip.id,
                'employee_id': employee_id,
                'pay_period': pay_period
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error saving payslip: {str(e)}'
            }, status=400)

    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)

@login_required(login_url='login')
def view_payslips(request):
    if not request.user.is_superuser:
        logout(request)
        # Don't add error message to prevent it from showing on login page
        return redirect('login')

    # Get filter parameters
    search_name = request.GET.get('search_name', '').strip()
    filter_month = request.GET.get('filter_month', '')
    filter_year = request.GET.get('filter_year', '')

    # Start with all payslips
    payslips = Payslip.objects.all().order_by('-created_at')

    # Apply filters if provided
    if search_name:
        # Search in both employee name and employee ID
        payslips = payslips.filter(
            Q(employee_name__icontains=search_name) |
            Q(employee_id__icontains=search_name)
        )

    if filter_month and filter_year:
        # Filter by specific month and year from pay_period
        month_map = {
            '01': 'Jan', '02': 'Feb', '03': 'Mar', '04': 'Apr',
            '05': 'May', '06': 'Jun', '07': 'Jul', '08': 'Aug',
            '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec'
        }
        month_name = month_map.get(filter_month, '')
        if month_name:
            payslips = payslips.filter(pay_period__icontains=f'{month_name}-{filter_year}')

    # Get unique months and years for filter dropdowns
    all_payslips = Payslip.objects.all()
    months = []
    years = []

    for payslip in all_payslips:
        # Extract month and year from pay_period (format: "1-Oct-2025 to 30-Oct-2025")
        pay_period = payslip.pay_period
        if ' to ' in pay_period:
            date_part = pay_period.split(' to ')[0]  # Get "1-Oct-2025"
            if '-' in date_part:
                parts = date_part.split('-')
                if len(parts) >= 2:
                    month_name = parts[1]
                    year = parts[2] if len(parts) > 2 else ''

                    # Convert month name to number
                    month_num = None
                    for num, name in [('01', 'Jan'), ('02', 'Feb'), ('03', 'Mar'), ('04', 'Apr'),
                                     ('05', 'May'), ('06', 'Jun'), ('07', 'Jul'), ('08', 'Aug'),
                                     ('09', 'Sep'), ('10', 'Oct'), ('11', 'Nov'), ('12', 'Dec')]:
                        if name == month_name:
                            month_num = num
                            break

                    if month_num and year:
                        if month_num not in months:
                            months.append(month_num)
                        if year not in years:
                            years.append(year)

    # Sort months and years
    months.sort()
    years.sort(reverse=True)  # Most recent years first

    context = {
        'payslips': payslips,
        'search_name': search_name,
        'filter_month': filter_month,
        'filter_year': filter_year,
        'available_months': months,
        'available_years': years,
    }

    return render(request, 'view_payslips.html', context)

@login_required(login_url='login')
def payslip_detail(request, payslip_id):
    """Display detailed view of a specific payslip"""
    if not request.user.is_superuser:
        logout(request)
        # Don't add error message to prevent it from showing on login page
        return redirect('login')

    try:
        payslip = Payslip.objects.get(id=payslip_id)

        # Check if PDF file exists
        pdf_file_exists = False
        if payslip.pdf_file and os.path.exists(payslip.pdf_file.path):
            pdf_file_exists = True

        # Prepare context data for the template
        context = {
            'payslip': payslip,
            'pdf_file_exists': pdf_file_exists,
            'payslip_data': {
                'employee_name': payslip.employee_name,
                'employee_id': payslip.employee_id,
                'pay_period': payslip.pay_period,
                'paid_days': payslip.paid_days,
                'loss_of_pay_days': payslip.loss_of_pay_days,
                'payment_date': payslip.payment_date,
                'basic_salary': payslip.basic_salary,
                'incentive': payslip.incentive,
                'gross_earnings': payslip.gross_earnings,
                'income_tax': payslip.income_tax,
                'total_deduction': payslip.total_deduction,
                'net_payable': payslip.net_payable,
                'amount_in_words': payslip.amount_in_words,
            }
        }

        return render(request, 'payslip_detail.html', context)

    except Payslip.DoesNotExist:
        # Don't add error message to prevent it from persisting to login page
        # messages.error(request, 'Payslip not found.')
        return redirect('view_payslips')
    except Exception as e:
        # Don't add error message to prevent it from persisting to login page
        # messages.error(request, f'Error loading payslip: {str(e)}')
        return redirect('view_payslips')

@login_required(login_url='login')
def delete_payslip(request, payslip_id):
    """Delete a specific payslip"""
    if not request.user.is_superuser:
        logout(request)
        # Don't add error message to prevent it from persisting to login page
        return redirect('login')

    try:
        payslip = Payslip.objects.get(id=payslip_id)

        # Store payslip info for success message
        employee_name = payslip.employee_name
        employee_id = payslip.employee_id
        pay_period = payslip.pay_period

        # Delete the PDF file if it exists
        if payslip.pdf_file and os.path.exists(payslip.pdf_file.path):
            try:
                os.remove(payslip.pdf_file.path)
            except OSError:
                pass  # File might not exist or couldn't be deleted

        # Delete the payslip record
        payslip.delete()

        # Don't add success message to prevent it from persisting to login page
        # messages.success(request,
        #     f'Payslip for {employee_name} (ID: {employee_id}) for period {pay_period} has been deleted successfully.')

    except Payslip.DoesNotExist:
        # Don't add error message to prevent it from persisting to login page
        # messages.error(request, 'Payslip not found.')
        pass
    except Exception as e:
        # Don't add error message to prevent it from persisting to login page
        # messages.error(request, f'Error deleting payslip: {str(e)}')
        pass

    return redirect('view_payslips')
