from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Booking
import re

class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Password'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Confirm Password'}))
    
    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'Email (Optional)'}),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("A user with that username already exists.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class BookingDetailsForm(forms.ModelForm):
    quantity = forms.IntegerField(
        initial=1,
        required=False,
        widget=forms.HiddenInput(),
        label="Number of Vehicles"
    )
    customer_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'Email Address (Optional)'}),
        label="Email Address"
    )
    customer_phone = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Phone Number (Required)'}),
        label="Phone Number"
    )

    id_proof_2 = forms.FileField(required=False, widget=forms.FileInput(attrs={'class': 'form-input-file', 'accept': '.pdf,.jpg,.jpeg,.png', 'id': 'id_id_proof_2'}))
    id_proof_3 = forms.FileField(required=False, widget=forms.FileInput(attrs={'class': 'form-input-file', 'accept': '.pdf,.jpg,.jpeg,.png', 'id': 'id_id_proof_3'}))
    id_proof_4 = forms.FileField(required=False, widget=forms.FileInput(attrs={'class': 'form-input-file', 'accept': '.pdf,.jpg,.jpeg,.png', 'id': 'id_id_proof_4'}))
    id_proof_5 = forms.FileField(required=False, widget=forms.FileInput(attrs={'class': 'form-input-file', 'accept': '.pdf,.jpg,.jpeg,.png', 'id': 'id_id_proof_5'}))

    class Meta:
        model = Booking
        fields = [
            'start_date', 'end_date', 'start_time', 'end_time', 'quantity',
            'customer_name', 'customer_age', 'customer_gender', 'customer_email', 'customer_phone', 'customer_address', 
            'id_proof', 'id_proof_2', 'id_proof_3', 'id_proof_4', 'id_proof_5'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-input'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-input'}),
            'customer_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Your Full Name'}),
            'customer_age': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Your Age'}),
            'customer_gender': forms.Select(attrs={'class': 'form-input'}),
            'customer_address': forms.Textarea(attrs={'class': 'form-input', 'placeholder': 'Your Full Address (30-100 characters)', 'rows': 3}),
            'id_proof': forms.FileInput(attrs={'class': 'form-input-file', 'accept': '.pdf,.jpg,.jpeg,.png', 'id': 'id_id_proof_1'}),
            'id_proof_2': forms.FileInput(attrs={'class': 'form-input-file', 'accept': '.pdf,.jpg,.jpeg,.png', 'id': 'id_id_proof_2'}),
            'id_proof_3': forms.FileInput(attrs={'class': 'form-input-file', 'accept': '.pdf,.jpg,.jpeg,.png', 'id': 'id_id_proof_3'}),
            'id_proof_4': forms.FileInput(attrs={'class': 'form-input-file', 'accept': '.pdf,.jpg,.jpeg,.png', 'id': 'id_id_proof_4'}),
            'id_proof_5': forms.FileInput(attrs={'class': 'form-input-file', 'accept': '.pdf,.jpg,.jpeg,.png', 'id': 'id_id_proof_5'}),
        }

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is None:
            return 1
        if quantity < 1 or quantity > 5:
            raise ValidationError("Please select a quantity between 1 and 5.")
        return quantity

    def clean_customer_phone(self):
        phone = self.cleaned_data.get('customer_phone')
        if not phone:
            raise ValidationError("Phone number is required.")
        phone_digits = re.sub(r'[\s\-]', '', phone)
        if not phone_digits.isdigit():
            raise ValidationError("Phone number must contain only digits.")
        if len(phone_digits) < 10 or len(phone_digits) > 15:
            raise ValidationError("Phone number must be between 10 and 15 digits.")
        return phone_digits

    def clean_customer_name(self):
        name = self.cleaned_data.get('customer_name')
        if len(name) < 10 or len(name) > 30:
            raise ValidationError("Name must be between 10 and 30 characters long.")
        return name

    def clean_customer_age(self):
        age = self.cleaned_data.get('customer_age')
        if age < 18:
            raise ValidationError("You must be at least 18 years old to rent a vehicle.")
        if age > 75:
            raise ValidationError("You must not be older than 75 years to rent a vehicle.")
        return age

    def clean_customer_address(self):
        address = self.cleaned_data.get('customer_address')
        if len(address) < 30 or len(address) > 100:
            raise ValidationError("Address must be between 30 and 100 characters long.")
        return address

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        today = timezone.localdate()
        
        if start_date:
            if start_date < today:
                self.add_error('start_date', "Start date cannot be in the past.")
        
        if start_date and end_date:
            if end_date < start_date:
                self.add_error('end_date', "End date cannot be earlier than start date.")
            elif start_date == end_date:
                if start_time and end_time and end_time <= start_time:
                    self.add_error('end_time', "End time must be after start time for the same day booking.")
                    
        return cleaned_data


class PaymentForm(forms.Form):
    PAYMENT_CHOICES = [
        ('UPI', 'UPI'),
        ('Netbanking', 'Netbanking'),
        ('Card', 'Credit/Debit Card'),
        ('Pay on Visit', 'Pay on Visit (+₹50 Extra)')
    ]
    
    payment_method = forms.ChoiceField(
        choices=PAYMENT_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'payment-radio'})
    )
    
    # UPI fields
    upi_id = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'username@bank'})
    )
    utr_id = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Enter 12-Digit UTR ID', 'maxlength': '12'})
    )
    
    # Netbanking fields
    bank_name = forms.ChoiceField(
        choices=[('', 'Select Bank'), ('SBI', 'State Bank of India'), ('HDFC', 'HDFC Bank'), ('ICICI', 'ICICI Bank'), ('AXIS', 'Axis Bank')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    
    # Card fields
    card_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': '12-16 Digit Card Number', 'maxlength': '16'})
    )
    card_expiry = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'MM/YY', 'maxlength': '5'})
    )
    card_cvv = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'CVV', 'maxlength': '4'}),
        label="CVV"
    )

    def __init__(self, *args, **kwargs):
        self.total_vehicles = kwargs.pop('total_vehicles', 1)
        super().__init__(*args, **kwargs)
        if self.total_vehicles >= 2:
            self.fields['payment_amount_choice'] = forms.ChoiceField(
                choices=[
                    ('100', 'Pay Full Amount (100%)'),
                    ('25', 'Pay Minimum Prepayment (25%) - Balance on visit')
                ],
                widget=forms.RadioSelect(attrs={'class': 'payment-choice-radio'}),
                initial='100',
                required=False
            )

    def clean(self):
        cleaned_data = super().clean()
        method = cleaned_data.get('payment_method')
        
        if self.total_vehicles >= 2 and method == 'Pay on Visit':
            self.add_error('payment_method', "Pay on Visit is not allowed for 2 or more vehicles. You must prepay at least 25% online.")
        
        if method == 'UPI':
            upi_id = cleaned_data.get('upi_id')
            utr_id = cleaned_data.get('utr_id')
            if not upi_id:
                self.add_error('upi_id', "UPI ID is required for UPI payments.")
            elif not re.match(r'^[\w\.\-]+@[\w\-]+$', upi_id):
                self.add_error('upi_id', "Enter a valid UPI ID (e.g. name@bank).")
                
            if not utr_id:
                self.add_error('utr_id', "UTR ID is required for UPI payments.")
            elif not utr_id.isdigit() or len(utr_id) != 12:
                self.add_error('utr_id', "UTR ID must be exactly 12 numeric digits.")
                
        elif method == 'Netbanking':
            bank = cleaned_data.get('bank_name')
            if not bank:
                self.add_error('bank_name', "Please select your bank.")
                
        elif method == 'Card':
            card_num = cleaned_data.get('card_number')
            cvv = cleaned_data.get('card_cvv')
            expiry = cleaned_data.get('card_expiry')
            
            # Remove spaces/dashes
            if card_num:
                card_num = re.sub(r'[\s\-]', '', card_num)
                
            if not card_num:
                self.add_error('card_number', "Card number is required.")
            elif not card_num.isdigit() or len(card_num) < 12:
                self.add_error('card_number', "Card number must contain at least 12 digits.")
                
            if not cvv:
                self.add_error('card_cvv', "CVV is required.")
            elif not cvv.isdigit() or len(cvv) < 3:
                self.add_error('card_cvv', "CVV must be at least 3 digits.")
                
            if not expiry:
                self.add_error('card_expiry', "Expiry date is required.")
            elif not re.match(r'^(0[1-9]|1[0-2])\/?([0-9]{2})$', expiry):
                self.add_error('card_expiry', "Expiry must be in MM/YY format.")
                
        return cleaned_data


class RejectionForm(forms.Form):
    REASON_CHOICES = [
        ('Vehicle Not Available', 'Vehicle Not Available'),
        ('Invalid ID Proof', 'Invalid ID Proof'),
        ('Maintenance Required', 'Maintenance Required'),
        ('Other', 'Other (Please specify below)'),
    ]
    
    predefined_reason = forms.ChoiceField(
        choices=REASON_CHOICES,
        widget=forms.Select(attrs={'class': 'form-input', 'id': 'id_predefined_reason'}),
        label="Reason for Rejection"
    )
    
    custom_description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-input', 'placeholder': 'Provide specific details...', 'rows': 3, 'id': 'id_custom_description'}),
        label="Custom Description"
    )

    def clean(self):
        cleaned_data = super().clean()
        predefined = cleaned_data.get('predefined_reason')
        custom = cleaned_data.get('custom_description')
        
        if predefined == 'Other' and not custom:
            self.add_error('custom_description', "Please provide a description when selecting 'Other'.")
            
        return cleaned_data

class CancelModifyForm(forms.Form):
    REASON_CHOICES = [
        ('Date selection wrong', 'Date selection wrong'),
        ('Time selection wrong', 'Time selection wrong'),
        ('Other', 'Other (Please specify)'),
    ]
    
    reason = forms.ChoiceField(
        choices=REASON_CHOICES,
        widget=forms.Select(attrs={'class': 'form-input', 'id': 'id_cancel_reason'})
    )
    
    new_start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-input', 'id': 'id_new_start_date'})
    )
    new_end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-input', 'id': 'id_new_end_date'})
    )
    
    new_start_time = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-input', 'id': 'id_new_start_time'})
    )
    new_end_time = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-input', 'id': 'id_new_end_time'})
    )
    
    custom_reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-input', 'placeholder': 'Reason for cancellation...', 'rows': 3, 'id': 'id_custom_reason'})
    )

    def clean(self):
        cleaned_data = super().clean()
        reason = cleaned_data.get('reason')
        
        if reason == 'Date selection wrong':
            nsd = cleaned_data.get('new_start_date')
            ned = cleaned_data.get('new_end_date')
            if not nsd:
                self.add_error('new_start_date', 'Please provide a new start date.')
            if not ned:
                self.add_error('new_end_date', 'Please provide a new end date.')
                
            today = timezone.localdate()
            if nsd and nsd < today:
                self.add_error('new_start_date', "Start date cannot be in the past.")
            if nsd and ned and ned < nsd:
                self.add_error('new_end_date', "End date cannot be earlier than start date.")
                
        elif reason == 'Time selection wrong':
            nst = cleaned_data.get('new_start_time')
            net = cleaned_data.get('new_end_time')
            if not nst:
                self.add_error('new_start_time', 'Please provide a new start time.')
            if not net:
                self.add_error('new_end_time', 'Please provide a new end time.')
                
        elif reason == 'Other':
            cr = cleaned_data.get('custom_reason')
            if not cr:
                self.add_error('custom_reason', 'Please provide a reason for cancellation.')
                
        return cleaned_data

