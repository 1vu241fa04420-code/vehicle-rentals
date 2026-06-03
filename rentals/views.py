from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache

from .models import Vehicle, Booking
from .forms import RegistrationForm, BookingDetailsForm, PaymentForm, RejectionForm, CancelModifyForm
from django.contrib.auth.forms import AuthenticationForm
from functools import wraps

def location_verified_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.is_staff:
            if not request.session.get('location_verified'):
                messages.warning(request, "Please verify your location to proceed with renting vehicles.")
                return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@never_cache
def login_signup_view(request):
    # Redirect if already logged in
    if request.user.is_authenticated:
        return redirect('home')

    login_form = AuthenticationForm()
    signup_form = RegistrationForm()
    active_tab = 'login'

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'signup':
            active_tab = 'signup'
            signup_form = RegistrationForm(request.POST)
            if signup_form.is_valid():
                signup_form.save()
                messages.success(request, "Sign up completed successfully! You can now login with your details.")
                return redirect('login')
        elif action == 'login':
            active_tab = 'login'
            login_form = AuthenticationForm(request, data=request.POST)
            if login_form.is_valid():
                username = login_form.cleaned_data.get('username')
                password = login_form.cleaned_data.get('password')
                user = authenticate(username=username, password=password)
                if user is not None:
                    login(request, user)
                    return redirect('home')
            else:
                messages.error(request, "Invalid username or password.")
        elif action == 'admin_login':
            active_tab = 'admin'
            login_form = AuthenticationForm(request, data=request.POST)
            if login_form.is_valid():
                username = login_form.cleaned_data.get('username')
                password = login_form.cleaned_data.get('password')
                user = authenticate(username=username, password=password)
                if user is not None:
                    if user.is_staff:
                        login(request, user)
                        messages.success(request, "Admin login successful!")
                        return redirect('home')
                    else:
                        messages.error(request, "Access denied. You do not have administrator privileges.")
                else:
                    messages.error(request, "Invalid username or password.")
            else:
                messages.error(request, "Invalid username or password.")

    return render(request, 'auth/login_signup.html', {
        'login_form': login_form,
        'signup_form': signup_form,
        'active_tab': active_tab
    })

@never_cache
def logout_view(request):
    request.session.flush()
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect('login')

@login_required
@require_POST
def verify_location_view(request):
    request.session['location_verified'] = True
    return JsonResponse({'status': 'success'})

@login_required
@never_cache
def home(request):
    if request.user.is_staff:
        bookings = Booking.objects.exclude(payment_status='Pending').order_by('-created_at')
        return render(request, 'admin_dashboard.html', {
            'bookings': bookings
        })
        
    # Fetch all confirmed/completed bookings for this user that are not deleted from dashboard
    # Note: exclude 'Pending' which indicates incomplete wizard sessions
    bookings = request.user.bookings.exclude(payment_status='Pending').filter(is_deleted_by_user=False).order_by('-created_at')
    recent_booking = bookings.first() if bookings.exists() else None
    
    return render(request, 'home.html', {
        'bookings': bookings,
        'recent_booking': recent_booking
    })

@login_required
@location_verified_required
@never_cache
def select_type(request):
    if request.method == 'POST':
        vehicle_type = request.POST.get('vehicle_type')
        if vehicle_type in ['car', 'bike']:
            request.session['booking_vehicle_type'] = vehicle_type
            return redirect('select_model')
    return render(request, 'wizard/select_type.html')

@login_required
@location_verified_required
@never_cache
def select_model(request):
    vehicle_type = request.session.get('booking_vehicle_type')
    if not vehicle_type:
        return redirect('select_type')
        
    # Initialize availability for each vehicle of the current type in session if not set
    availabilities = request.session.get('vehicle_availabilities', {})
    import random
    changed = False
    
    vehicles = Vehicle.objects.filter(vehicle_type=vehicle_type)
    for vehicle in vehicles:
        v_id_str = str(vehicle.id)
        if v_id_str not in availabilities:
            availabilities[v_id_str] = random.randint(2, 5)
            changed = True
            
    if changed:
        request.session['vehicle_availabilities'] = availabilities
        request.session.modified = True
        
    if request.method == 'POST':
        # Retrieve or initialize session selections
        selections = request.session.get('selected_vehicles', {})
        
        # Read all quantities for vehicles of this type
        for vehicle in vehicles:
            qty_val = request.POST.get(f'qty_{vehicle.id}', '0')
            try:
                qty_val = int(qty_val)
                # Cap qty at availability limit
                max_avail = availabilities.get(str(vehicle.id), 5)
                if qty_val > max_avail:
                    qty_val = max_avail
                
                if qty_val > 0:
                    selections[str(vehicle.id)] = qty_val
                elif str(vehicle.id) in selections:
                    del selections[str(vehicle.id)]
            except ValueError:
                pass
                
        request.session['selected_vehicles'] = selections
        
        action = request.POST.get('action', 'proceed')
        if action == 'switch_type':
            # Toggle type
            new_type = 'bike' if vehicle_type == 'car' else 'car'
            request.session['booking_vehicle_type'] = new_type
            return redirect('select_model')
        elif action == 'clear_back':
            # Clear selections and go back
            request.session['selected_vehicles'] = {}
            return redirect('select_type')
        else:
            # Proceed to Rent Details
            return redirect('booking_details_multi')
            
    # GET request
    selections = request.session.get('selected_vehicles', {})
    
    # Pre-populate quantities and attach availability from session
    for v in vehicles:
        v.current_qty = selections.get(str(v.id), 0)
        v.availability = availabilities.get(str(v.id), 5)
        
    total_selected = sum(selections.values())
    
    return render(request, 'wizard/select_model.html', {
        'vehicles': vehicles,
        'vehicle_type': vehicle_type,
        'total_selected': total_selected
    })

@login_required
def remove_selected_vehicle(request, vehicle_id):
    selections = request.session.get('selected_vehicles', {})
    vid_str = str(vehicle_id)
    if vid_str in selections:
        del selections[vid_str]
        request.session['selected_vehicles'] = selections
        request.session.modified = True
        
        # Display feedback message
        try:
            vehicle = Vehicle.objects.get(id=vehicle_id)
            messages.success(request, f"{vehicle.name} has been removed from your selection.")
        except Vehicle.DoesNotExist:
            messages.success(request, "Vehicle removed from selection.")
            
    if selections:
        return redirect('booking_details_multi')
    else:
        return redirect('select_type')

@login_required
@location_verified_required
@never_cache
def booking_details_multi(request):
    selections = request.session.get('selected_vehicles', {})
    if not selections:
        return redirect('select_type')
        
    # Check if there is already a pending booking in the cart
    cart_items = Booking.objects.filter(user=request.user, payment_status='Pending').order_by('-created_at')
    
    if cart_items.exists():
        first_booking = cart_items.first()
        
        # Clone details for all selected items
        for vid, qty in selections.items():
            vehicle = get_object_or_404(Vehicle, id=int(vid))
            booking = Booking.objects.create(
                user=request.user,
                vehicle=vehicle,
                start_date=first_booking.start_date,
                end_date=first_booking.end_date,
                start_time=first_booking.start_time,
                end_time=first_booking.end_time,
                quantity=qty,
                customer_name=first_booking.customer_name,
                customer_age=first_booking.customer_age,
                customer_gender=first_booking.customer_gender,
                customer_email=first_booking.customer_email,
                customer_phone=first_booking.customer_phone,
                customer_address=first_booking.customer_address,
                id_proof=first_booking.id_proof,
                num_days=first_booking.num_days,
                base_amount=first_booking.num_days * vehicle.price_per_day * qty,
                total_amount=first_booking.num_days * vehicle.price_per_day * qty,
                payment_status='Pending'
            )
            
        # Clear selection session values
        for key in ['booking_vehicle_type', 'booking_vehicle_id', 'selected_vehicles']:
            if key in request.session:
                del request.session[key]
                
        messages.success(request, "Selected vehicles have been added to your cart using your existing rental details.")
        return redirect('cart')
        
    # Get all vehicle objects and attach their quantities
    selected_items = []
    availabilities = request.session.get('vehicle_availabilities', {})
    for vid, qty in selections.items():
        vehicle = get_object_or_404(Vehicle, id=int(vid))
        # Attach availability
        vehicle.availability = availabilities.get(str(vehicle.id), 5)
        # Cap selection if it exceeds availability
        if qty > vehicle.availability:
            qty = vehicle.availability
            selections[str(vid)] = qty
            request.session['selected_vehicles'] = selections
            request.session.modified = True
        selected_items.append({'vehicle': vehicle, 'quantity': qty})
        
    if request.method == 'POST':
        form = BookingDetailsForm(request.POST, request.FILES)
        if form.is_valid():
            # Collect all valid uploaded ID proofs
            all_id_proofs = [
                form.cleaned_data.get('id_proof'),
                form.cleaned_data.get('id_proof_2'),
                form.cleaned_data.get('id_proof_3'),
                form.cleaned_data.get('id_proof_4'),
                form.cleaned_data.get('id_proof_5'),
            ]
            all_id_proofs = [p for p in all_id_proofs if p]
            
            proof_index = 0
            
            # Create bookings for all selected vehicles!
            for item in selected_items:
                vehicle = item['vehicle']
                qty = item['quantity']
                
                # Take up to 'qty' proofs for this booking
                booking_proofs = all_id_proofs[proof_index:proof_index + qty]
                proof_index += qty
                
                # Pad to 5 elements to avoid IndexError
                while len(booking_proofs) < 5:
                    booking_proofs.append(None)
                
                # Create a booking instance
                booking = Booking(
                    user=request.user,
                    vehicle=vehicle,
                    start_date=form.cleaned_data['start_date'],
                    end_date=form.cleaned_data['end_date'],
                    start_time=form.cleaned_data['start_time'],
                    end_time=form.cleaned_data['end_time'],
                    quantity=qty,
                    customer_name=form.cleaned_data['customer_name'],
                    customer_age=form.cleaned_data['customer_age'],
                    customer_gender=form.cleaned_data['customer_gender'],
                    customer_email=form.cleaned_data['customer_email'],
                    customer_phone=form.cleaned_data['customer_phone'],
                    customer_address=form.cleaned_data['customer_address'],
                    id_proof=booking_proofs[0],
                    id_proof_2=booking_proofs[1],
                    id_proof_3=booking_proofs[2],
                    id_proof_4=booking_proofs[3],
                    id_proof_5=booking_proofs[4],
                )
                
                # Calculate days
                delta = booking.end_date - booking.start_date
                num_days = delta.days
                if num_days == 0:
                    num_days = 1
                booking.num_days = num_days
                
                # Calculations
                booking.base_amount = num_days * vehicle.price_per_day * qty
                booking.total_amount = booking.base_amount
                booking.payment_status = 'Pending'
                booking.save()
                
            # Clear selection session values
            for key in ['booking_vehicle_type', 'booking_vehicle_id', 'selected_vehicles']:
                if key in request.session:
                    del request.session[key]
                    
            messages.success(request, f"Your vehicle bookings have been added to your cart.")
            return redirect('cart')
    else:
        form = BookingDetailsForm()
        
    total_vehicle_count = sum(item['quantity'] for item in selected_items)
    
    return render(request, 'wizard/booking_form.html', {
        'form': form,
        'selected_items': selected_items,
        'total_vehicle_count': total_vehicle_count
    })

@login_required
@location_verified_required
@never_cache
def booking_details(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    request.session['booking_vehicle_id'] = vehicle_id
    
    # Initialize availability for this vehicle in session if not set
    availabilities = request.session.get('vehicle_availabilities', {})
    v_id_str = str(vehicle.id)
    if v_id_str not in availabilities:
        import random
        availabilities[v_id_str] = random.randint(2, 5)
        request.session['vehicle_availabilities'] = availabilities
        request.session.modified = True
    vehicle.availability = availabilities[v_id_str]
    
    # Check if there is already a pending booking in the cart
    cart_items = Booking.objects.filter(user=request.user, payment_status='Pending').order_by('-created_at')
    
    if cart_items.exists():
        # Get requested quantity from query params
        qty = request.GET.get('quantity', 1)
        try:
            qty = int(qty)
            if qty < 1 or qty > vehicle.availability:
                qty = 1
        except (TypeError, ValueError):
            qty = 1
            
        first_booking = cart_items.first()
        
        # Clone booking details immediately
        booking = Booking.objects.create(
            user=request.user,
            vehicle=vehicle,
            start_date=first_booking.start_date,
            end_date=first_booking.end_date,
            start_time=first_booking.start_time,
            end_time=first_booking.end_time,
            quantity=qty,
            customer_name=first_booking.customer_name,
            customer_age=first_booking.customer_age,
            customer_gender=first_booking.customer_gender,
            customer_email=first_booking.customer_email,
            customer_phone=first_booking.customer_phone,
            customer_address=first_booking.customer_address,
            id_proof=first_booking.id_proof,
            num_days=first_booking.num_days,
            base_amount=first_booking.num_days * vehicle.price_per_day * qty,
            total_amount=first_booking.num_days * vehicle.price_per_day * qty,
            payment_status='Pending'
        )
        
        # Clean up session values for this specific booking addition
        for key in ['booking_vehicle_type', 'booking_vehicle_id']:
            if key in request.session:
                del request.session[key]
                
        messages.success(request, f"{vehicle.name} has been added to your cart using your existing rental details.")
        return redirect('cart')
        
    if request.method == 'POST':
        form = BookingDetailsForm(request.POST, request.FILES)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.vehicle = vehicle
            
            # Calculate days
            delta = booking.end_date - booking.start_date
            num_days = delta.days
            if num_days == 0:
                num_days = 1
            booking.num_days = num_days
            
            # Base financial calculations
            booking.base_amount = num_days * vehicle.price_per_day * booking.quantity
            booking.total_amount = booking.base_amount
            booking.payment_status = 'Pending'
            booking.save()
            
            # Clean up session values for this specific booking addition
            for key in ['booking_vehicle_type', 'booking_vehicle_id']:
                if key in request.session:
                    del request.session[key]
                    
            messages.success(request, f"{vehicle.name} has been added to your cart.")
            return redirect('cart')
    else:
        qty = request.GET.get('quantity', 1)
        try:
            qty = int(qty)
            if qty < 1 or qty > vehicle.availability:
                qty = 1
        except (TypeError, ValueError):
            qty = 1
        form = BookingDetailsForm(initial={'quantity': qty})
        
    return render(request, 'wizard/booking_form.html', {
        'form': form,
        'vehicle': vehicle
    })

@login_required
@location_verified_required
@never_cache
def cart_view(request):
    cart_items = Booking.objects.filter(user=request.user, payment_status='Pending').order_by('-created_at')
    grand_total = sum(item.base_amount for item in cart_items)
    
    return render(request, 'wizard/cart.html', {
        'cart_items': cart_items,
        'grand_total': grand_total
    })

@login_required
def remove_from_cart(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user, payment_status='Pending')
    vehicle_name = booking.vehicle.name
    booking.delete()
    messages.success(request, f"{vehicle_name} has been removed from your cart.")
    return redirect('cart')

@login_required
@location_verified_required
@never_cache
def billing_receipt(request):
    cart_items = Booking.objects.filter(user=request.user, payment_status='Pending').order_by('-created_at')
    if not cart_items.exists():
        return redirect('home')
        
    grand_total = sum(item.base_amount for item in cart_items)
    return render(request, 'wizard/receipt.html', {
        'cart_items': cart_items,
        'grand_total': grand_total
    })

@login_required
@location_verified_required
@never_cache
def payment_processing(request):
    from decimal import Decimal
    cart_items = Booking.objects.filter(user=request.user, payment_status='Pending').order_by('-created_at')
    if not cart_items.exists():
        return redirect('home')
        
    grand_total = sum(item.base_amount for item in cart_items)
    total_vehicles = sum(item.quantity for item in cart_items)
    
    if request.method == 'POST':
        form = PaymentForm(request.POST, total_vehicles=total_vehicles)
        if form.is_valid():
            payment_method = form.cleaned_data['payment_method']
            payment_choice = form.cleaned_data.get('payment_amount_choice', '100')
            
            for i, booking in enumerate(cart_items):
                booking.payment_method = payment_method
                if payment_method == 'Pay on Visit':
                    if i == 0:
                        booking.extra_charge = Decimal('50.00')
                        booking.total_amount = booking.base_amount + Decimal('50.00')
                    else:
                        booking.extra_charge = Decimal('0.00')
                        booking.total_amount = booking.base_amount
                    booking.prepaid_amount = Decimal('0.00')
                else:
                    booking.extra_charge = Decimal('0.00')
                    booking.total_amount = booking.base_amount
                    if total_vehicles >= 2 and payment_choice == '25':
                        booking.prepaid_amount = booking.total_amount * Decimal('0.25')
                    else:
                        booking.prepaid_amount = booking.total_amount
                
                # Save UTR ID if method is UPI
                if payment_method == 'UPI':
                    booking.utr_id = form.cleaned_data.get('utr_id')
                else:
                    booking.utr_id = None
                
                booking.save()
                
            # Store selected payment method in session for the portal display
            request.session['selected_payment_method'] = payment_method
            request.session['selected_payment_choice'] = payment_choice
            return redirect('payment_portal')
    else:
        form = PaymentForm(initial={'payment_method': 'UPI', 'upi_id': '7337060329@ibl'}, total_vehicles=total_vehicles)
        
    return render(request, 'wizard/payment.html', {
        'form': form,
        'cart_items': cart_items,
        'grand_total': grand_total,
        'total_vehicles': total_vehicles
    })

@login_required
@location_verified_required
@never_cache
def payment_portal(request):
    cart_items = Booking.objects.filter(user=request.user, payment_status='Pending')
    if not cart_items.exists():
        return redirect('home')
        
    payment_method = request.session.get('selected_payment_method')
    grand_total = sum(item.total_amount for item in cart_items)
    
    return render(request, 'wizard/payment_portal.html', {
        'cart_items': cart_items,
        'grand_total': grand_total,
        'payment_method': payment_method
    })

import sys

def safe_print(text):
    try:
        print(text)
    except Exception:
        pass

def send_whatsapp_message(phone_number, message_text):
    import urllib.request
    import urllib.parse
    import base64
    import json
    from django.conf import settings
    
    account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
    auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
    from_number = getattr(settings, 'TWILIO_FROM_NUMBER', '')
    
    # If not fully configured, fallback to simulation mode
    if not account_sid or not auth_token or not from_number:
        safe_print(f"[SIMULATION] WHATSAPP LOG: Sending WhatsApp message to {phone_number}...")
        safe_print(f"--- WHATSAPP MESSAGE START ---")
        safe_print(message_text)
        safe_print(f"--- WHATSAPP MESSAGE END ---")
        return
        
    # Standardize phone number format for Twilio (e.g. +917569291174)
    clean_phone = phone_number.strip().replace(" ", "").replace("-", "")
    if not clean_phone.startswith("+"):
        if len(clean_phone) == 10:
            clean_phone = "+91" + clean_phone
        else:
            clean_phone = "+" + clean_phone
            
    to_number = f"whatsapp:{clean_phone}"
    
    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    
    payload = urllib.parse.urlencode({
        'From': from_number,
        'To': to_number,
        'Body': message_text
    }).encode('utf-8')
    
    req = urllib.request.Request(url, data=payload, method='POST')
    
    # Add Authorization and Content-Type Headers
    auth_str = f"{account_sid}:{auth_token}"
    auth_b64 = base64.b64encode(auth_str.encode('utf-8')).decode('utf-8')
    req.add_header("Authorization", f"Basic {auth_b64}")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res_body = response.read().decode('utf-8')
            res_json = json.loads(res_body)
            safe_print(f"REAL WHATSAPP: Message successfully sent to {phone_number}. Twilio SID: {res_json.get('sid')}")
    except Exception as e:
        safe_print(f"REAL WHATSAPP ERROR: Failed to send to {phone_number}: {str(e)}")

def send_booking_notifications(booking):
    # 1. Send Email (if email is provided)
    if booking.customer_email:
        subject = f"Booking Confirmation #WWR-{booking.id} - Web Wizards Car Rentals"
        email_body = f"""Dear {booking.customer_name},

Thank you for booking with Web Wizards Car Rentals! Your reservation is confirmed.

Booking Details:
---------------------------------------------
Booking ID: #WWR-{booking.id}
Vehicle: {booking.vehicle.name} ({booking.vehicle.get_vehicle_type_display()})
Start Date: {booking.start_date} at {booking.start_time}
End Date: {booking.end_date} at {booking.end_time}
Duration: {booking.num_days} day(s)
Quantity: {booking.quantity}
Total Amount: Rs. {booking.total_amount}
Amount Paid Now: Rs. {booking.prepaid_amount}
Balance to Pay on Visit: Rs. {booking.balance_amount}
---------------------------------------------

Pickup Location:
Pattabhipuram 3rd line, Guntur, Andhra Pradesh - 522006
Besides DRM office.
Phone: 7337060329

If you have any questions, feel free to contact us.

Safe Travels,
Web Wizards Car Rentals Team"""
        
        try:
            from django.core.mail import send_mail
            from django.conf import settings
            send_mail(
                subject=subject,
                message=email_body,
                from_email=getattr(settings, 'EMAIL_HOST_USER', '1vu.241fa04420@gmail.com'),
                recipient_list=[booking.customer_email],
                fail_silently=True,
            )
            safe_print(f"EMAIL LOG: Sent booking confirmation email to {booking.customer_email} for Booking #WWR-{booking.id}")
        except Exception as e:
            safe_print(f"EMAIL ERROR: Failed to send email to {booking.customer_email}: {str(e)}")

    # 2. Send WhatsApp message (ASCII only to prevent terminal encoding crashes)
    whatsapp_text = f"""*Web Wizards Car Rentals - Booking Confirmed!*

Hello {booking.customer_name}, your booking #WWR-{booking.id} is confirmed.

*Vehicle:* {booking.vehicle.name}
*Dates:* {booking.start_date} to {booking.end_date}
*Total Amount:* Rs. {booking.total_amount}
*Amount Paid Now:* Rs. {booking.prepaid_amount}
*Balance to Pay on Visit:* Rs. {booking.balance_amount}
*Pickup Location:* Pattabhipuram 3rd line, Guntur, AP.

For support, call 7337060329. Thank you for renting with us!"""
    
    send_whatsapp_message(booking.customer_phone, whatsapp_text)

@login_required
@location_verified_required
@never_cache
def payment_success(request):
    cart_items = list(Booking.objects.filter(user=request.user, payment_status='Pending'))
    if not cart_items:
        return redirect('home')
        
    grand_total = sum(item.total_amount for item in cart_items)
    prepaid_total = sum(item.prepaid_amount for item in cart_items)
    balance = grand_total - prepaid_total
    
    for booking in cart_items:
        booking.payment_status = 'Completed'
        booking.save()
        safe_print(f"Conformation message sent to given mobile number and mail for Booking #WWR-{booking.id} to phone number {booking.customer_phone} (Customer: {booking.customer_name}, Amount Paid: Rs. {booking.prepaid_amount})")
        send_booking_notifications(booking)
        
    # Clean up session values for the wizard
    for key in ['booking_vehicle_type', 'booking_vehicle_id', 'selected_payment_method', 'selected_payment_choice']:
        if key in request.session:
            del request.session[key]
            
    return render(request, 'wizard/success.html', {
        'bookings': cart_items,
        'grand_total': grand_total,
        'prepaid_total': prepaid_total,
        'balance': balance,
    })


@login_required
def reject_booking(request, booking_id):
    if not request.user.is_staff:
        messages.error(request, "Access denied. Only administrators can perform this action.")
        return redirect('home')
        
    booking = get_object_or_404(Booking, id=booking_id)
    
    if request.method == 'POST':
        form = RejectionForm(request.POST)
        if form.is_valid():
            predefined = form.cleaned_data['predefined_reason']
            custom = form.cleaned_data['custom_description']
            
            if predefined == 'Other':
                reason = custom
            else:
                reason = predefined
                if custom:
                    reason = f"{predefined} - {custom}"
                    
            booking.status = 'Rejected'
            booking.rejection_reason = reason
            booking.save()
            
            messages.success(request, f"Booking #{booking.id} has been rejected.")
            return redirect('home')
    else:
        form = RejectionForm()
        
    return render(request, 'wizard/reject_booking.html', {
        'form': form,
        'booking': booking
    })

@login_required
def cancel_modify_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    if booking.status == 'Cancelled':
        messages.error(request, "This booking is already cancelled.")
        return redirect('home')
        
    if request.method == 'POST':
        form = CancelModifyForm(request.POST)
        if form.is_valid():
            reason = form.cleaned_data['reason']
            
            if reason == 'Date selection wrong':
                booking.start_date = form.cleaned_data['new_start_date']
                booking.end_date = form.cleaned_data['new_end_date']
                
                delta = booking.end_date - booking.start_date
                num_days = delta.days if delta.days > 0 else 1
                booking.num_days = num_days
                
                old_total = booking.total_amount
                booking.base_amount = num_days * booking.vehicle.price_per_day * booking.quantity
                booking.total_amount = booking.base_amount + booking.extra_charge
                booking.save()
                
                messages.success(request, f"Dates updated. New total is ₹{booking.total_amount} (was ₹{old_total}). Any difference will be settled on visit.")
                
            elif reason == 'Time selection wrong':
                booking.start_time = form.cleaned_data['new_start_time']
                booking.end_time = form.cleaned_data['new_end_time']
                booking.save()
                messages.success(request, "Booking times have been successfully updated.")
                
            elif reason == 'Other':
                booking.status = 'Cancelled'
                booking.rejection_reason = form.cleaned_data['custom_reason']
                booking.save()
                messages.success(request, "Your booking has been successfully cancelled.")
                
            return redirect('home')
    else:
        form = CancelModifyForm()
        
    return render(request, 'wizard/cancel_modify.html', {
        'form': form,
        'booking': booking
    })

@login_required
def delete_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    if not request.user.is_staff and booking.user != request.user:
        messages.error(request, "Access denied.")
        return redirect('home')
        
    if request.user.is_staff:
        booking.delete()
        messages.success(request, "Booking completely deleted from the database.")
    else:
        if booking.status in ['Cancelled', 'Rejected']:
            booking.is_deleted_by_user = True
            booking.save()
            request.session['last_deleted_booking_ids'] = [booking.id]
            messages.success(request, "Booking removed from dashboard.")
        else:
            messages.error(request, "Only cancelled or rejected bookings can be removed.")
    return redirect('home')


@login_required
def delete_all_bookings(request):
    if request.method == 'POST':
        if request.user.is_staff:
            count = Booking.objects.all().count()
            Booking.objects.all().delete()
            messages.success(request, f"Successfully deleted all bookings ({count} records) from the system.")
        else:
            user_bookings = request.user.bookings.exclude(payment_status='Pending').filter(is_deleted_by_user=False)
            booking_ids = list(user_bookings.values_list('id', flat=True))
            if booking_ids:
                user_bookings.update(is_deleted_by_user=True)
                request.session['last_deleted_booking_ids'] = booking_ids
                messages.success(request, f"Successfully removed all your bookings ({len(booking_ids)} records) from your dashboard.")
            else:
                messages.info(request, "No bookings to clear.")
            
    return redirect('home')


@login_required
def undo_delete_booking(request):
    booking_ids = request.session.get('last_deleted_booking_ids')
    if booking_ids:
        Booking.objects.filter(id__in=booking_ids, user=request.user).update(is_deleted_by_user=False)
        del request.session['last_deleted_booking_ids']
        messages.success(request, "Deletion undone successfully! Bookings restored to dashboard.")
    else:
        messages.error(request, "No deleted bookings found to restore.")
    return redirect('home')


@login_required
def dismiss_delete_booking(request):
    if 'last_deleted_booking_ids' in request.session:
        del request.session['last_deleted_booking_ids']
    return redirect('home')


