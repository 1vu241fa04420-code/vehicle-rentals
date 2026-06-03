from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator, MaxLengthValidator, MinValueValidator, MaxValueValidator

class Vehicle(models.Model):
    VEHICLE_TYPES = [
        ('car', 'Car'),
        ('bike', 'Bike'),
    ]
    name = models.CharField(max_length=100)
    vehicle_type = models.CharField(max_length=10, choices=VEHICLE_TYPES)
    price_per_day = models.DecimalField(max_digits=8, decimal_places=2)
    image_path = models.CharField(max_length=255)  # Path to generated static image asset
    mileage = models.CharField(max_length=50, default="")
    fuel_type = models.CharField(max_length=20, default="Petrol")
    description = models.TextField()

    def __str__(self):
        return f"{self.name} ({self.get_vehicle_type_display()})"

class Booking(models.Model):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
    ]
    PAYMENT_CHOICES = [
        ('UPI', 'UPI'),
        ('Netbanking', 'Netbanking'),
        ('Card', 'Credit/Debit Card'),
        ('Pay on Visit', 'Pay on Visit'),
    ]
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='bookings')
    start_date = models.DateField()
    end_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    num_days = models.IntegerField()
    quantity = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    
    # Customer Details
    customer_name = models.CharField(
        max_length=30,
        validators=[MinLengthValidator(10), MaxLengthValidator(30)]
    )
    customer_age = models.IntegerField(
        validators=[MinValueValidator(18), MaxValueValidator(75)]
    )
    customer_gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    customer_email = models.EmailField(blank=True, null=True)
    customer_phone = models.CharField(max_length=15)
    customer_address = models.TextField(
        validators=[MinLengthValidator(30), MaxLengthValidator(100)]
    )
    id_proof = models.FileField(upload_to='id_proofs/')
    id_proof_2 = models.FileField(upload_to='id_proofs/', blank=True, null=True)
    id_proof_3 = models.FileField(upload_to='id_proofs/', blank=True, null=True)
    id_proof_4 = models.FileField(upload_to='id_proofs/', blank=True, null=True)
    id_proof_5 = models.FileField(upload_to='id_proofs/', blank=True, null=True)
    
    # Financial details
    base_amount = models.DecimalField(max_digits=10, decimal_places=2)
    extra_charge = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    prepaid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    @property
    def balance_amount(self):
        return self.total_amount - self.prepaid_amount
    
    # Payment details
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES)
    payment_status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='Pending')
    utr_id = models.CharField(max_length=12, blank=True, null=True)
    
    # Booking Approval status
    BOOKING_STATUS_CHOICES = [
        ('Confirmed', 'Confirmed'),
        ('Rejected', 'Rejected'),
        ('Cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=15, choices=BOOKING_STATUS_CHOICES, default='Confirmed')
    rejection_reason = models.TextField(blank=True, null=True)
    is_deleted_by_user = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking {self.id} - {self.customer_name} ({self.vehicle.name})"
