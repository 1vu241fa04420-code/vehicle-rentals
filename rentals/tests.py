from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from rentals.models import Vehicle, Booking
from rentals.forms import BookingDetailsForm

class FormValidationTests(TestCase):
    def setUp(self):
        # Create a sample vehicle
        self.vehicle = Vehicle.objects.create(
            name="Tesla Model X",
            vehicle_type="car",
            price_per_day=4500.00,
            image_path="tesla_sedan.png",
            description="Luxury electric SUV."
        )
        self.mock_file = SimpleUploadedFile("id_proof.png", b"file_content", content_type="image/png")

    def test_booking_form_valid_data(self):
        today = timezone.localdate()
        form_data = {
            'start_date': today + timedelta(days=1),
            'end_date': today + timedelta(days=3),
            'start_time': '10:00',
            'end_time': '18:00',
            'customer_name': 'Johnathan Doe Smith',  # 19 characters (valid)
            'customer_age': 25,                      # >= 18 (valid)
            'customer_gender': 'Male',
            'customer_phone': '9876543210',          # required phone (valid)
            'customer_email': 'test@example.com',    # optional email (valid)
            'customer_address': '123 Cyberpunk Boulevard, Glassmorphism City, Sector 9',  # 55 characters (valid)
        }
        form = BookingDetailsForm(data=form_data, files={'id_proof': self.mock_file})
        self.assertTrue(form.is_valid(), form.errors.as_data())

    def test_booking_form_optional_email_empty(self):
        today = timezone.localdate()
        form_data = {
            'start_date': today + timedelta(days=1),
            'end_date': today + timedelta(days=3),
            'start_time': '10:00',
            'end_time': '18:00',
            'customer_name': 'Johnathan Doe Smith',
            'customer_age': 25,
            'customer_gender': 'Male',
            'customer_phone': '9876543210',
            'customer_email': '',                    # Empty email (valid because optional)
            'customer_address': '123 Cyberpunk Boulevard, Glassmorphism City, Sector 9',
        }
        form = BookingDetailsForm(data=form_data, files={'id_proof': self.mock_file})
        self.assertTrue(form.is_valid(), form.errors.as_data())

    def test_booking_form_invalid_phone_letters(self):
        today = timezone.localdate()
        form_data = {
            'start_date': today + timedelta(days=1),
            'end_date': today + timedelta(days=3),
            'start_time': '10:00',
            'end_time': '18:00',
            'customer_name': 'Johnathan Doe Smith',
            'customer_age': 25,
            'customer_gender': 'Male',
            'customer_phone': '987654321a',          # Contains letters (invalid)
            'customer_address': '123 Cyberpunk Boulevard, Glassmorphism City, Sector 9',
        }
        form = BookingDetailsForm(data=form_data, files={'id_proof': self.mock_file})
        self.assertFalse(form.is_valid())
        self.assertIn('customer_phone', form.errors)

    def test_booking_form_invalid_phone_short(self):
        today = timezone.localdate()
        form_data = {
            'start_date': today + timedelta(days=1),
            'end_date': today + timedelta(days=3),
            'start_time': '10:00',
            'end_time': '18:00',
            'customer_name': 'Johnathan Doe Smith',
            'customer_age': 25,
            'customer_gender': 'Male',
            'customer_phone': '9876543',             # Under 10 digits (invalid)
            'customer_address': '123 Cyberpunk Boulevard, Glassmorphism City, Sector 9',
        }
        form = BookingDetailsForm(data=form_data, files={'id_proof': self.mock_file})
        self.assertFalse(form.is_valid())
        self.assertIn('customer_phone', form.errors)

    def test_booking_form_invalid_name(self):
        today = timezone.localdate()
        form_data = {
            'start_date': today + timedelta(days=1),
            'end_date': today + timedelta(days=3),
            'start_time': '10:00',
            'end_time': '18:00',
            'customer_name': 'Short',  # Under 10 characters (invalid)
            'customer_age': 25,
            'customer_gender': 'Male',
            'customer_phone': '9876543210',
            'customer_address': '123 Cyberpunk Boulevard, Glassmorphism City, Sector 9',
        }
        form = BookingDetailsForm(data=form_data, files={'id_proof': self.mock_file})
        self.assertFalse(form.is_valid())
        self.assertIn('customer_name', form.errors)

    def test_booking_form_invalid_age_under(self):
        today = timezone.localdate()
        form_data = {
            'start_date': today + timedelta(days=1),
            'end_date': today + timedelta(days=3),
            'start_time': '10:00',
            'end_time': '18:00',
            'customer_name': 'Johnathan Doe Smith',
            'customer_age': 16,  # Under 18 (invalid)
            'customer_gender': 'Male',
            'customer_phone': '9876543210',
            'customer_address': '123 Cyberpunk Boulevard, Glassmorphism City, Sector 9',
        }
        form = BookingDetailsForm(data=form_data, files={'id_proof': self.mock_file})
        self.assertFalse(form.is_valid())
        self.assertIn('customer_age', form.errors)

    def test_booking_form_invalid_age_over(self):
        today = timezone.localdate()
        form_data = {
            'start_date': today + timedelta(days=1),
            'end_date': today + timedelta(days=3),
            'start_time': '10:00',
            'end_time': '18:00',
            'customer_name': 'Johnathan Doe Smith',
            'customer_age': 80,  # Over 75 (invalid)
            'customer_gender': 'Male',
            'customer_phone': '9876543210',
            'customer_address': '123 Cyberpunk Boulevard, Glassmorphism City, Sector 9',
        }
        form = BookingDetailsForm(data=form_data, files={'id_proof': self.mock_file})
        self.assertFalse(form.is_valid())
        self.assertIn('customer_age', form.errors)

    def test_booking_form_invalid_address(self):
        today = timezone.localdate()
        form_data = {
            'start_date': today + timedelta(days=1),
            'end_date': today + timedelta(days=3),
            'start_time': '10:00',
            'end_time': '18:00',
            'customer_name': 'Johnathan Doe Smith',
            'customer_age': 25,
            'customer_gender': 'Male',
            'customer_phone': '9876543210',
            'customer_address': 'Too Short Street',  # Under 30 characters (invalid)
        }
        form = BookingDetailsForm(data=form_data, files={'id_proof': self.mock_file})
        self.assertFalse(form.is_valid())
        self.assertIn('customer_address', form.errors)

    def test_booking_form_past_start_date(self):
        today = timezone.localdate()
        form_data = {
            'start_date': today - timedelta(days=1),  # Past date (invalid)
            'end_date': today + timedelta(days=2),
            'start_time': '10:00',
            'end_time': '18:00',
            'customer_name': 'Johnathan Doe Smith',
            'customer_age': 25,
            'customer_gender': 'Male',
            'customer_phone': '9876543210',
            'customer_address': '123 Cyberpunk Boulevard, Glassmorphism City, Sector 9',
        }
        form = BookingDetailsForm(data=form_data, files={'id_proof': self.mock_file})
        self.assertFalse(form.is_valid())
        self.assertIn('start_date', form.errors)

    def test_booking_form_end_before_start_date(self):
        today = timezone.localdate()
        form_data = {
            'start_date': today + timedelta(days=3),
            'end_date': today + timedelta(days=1),  # End before start (invalid)
            'start_time': '10:00',
            'end_time': '18:00',
            'customer_name': 'Johnathan Doe Smith',
            'customer_age': 25,
            'customer_gender': 'Male',
            'customer_phone': '9876543210',
            'customer_address': '123 Cyberpunk Boulevard, Glassmorphism City, Sector 9',
        }
        form = BookingDetailsForm(data=form_data, files={'id_proof': self.mock_file})
        self.assertFalse(form.is_valid())
        self.assertIn('end_date', form.errors)


from rentals.forms import RejectionForm

class RejectionFormTests(TestCase):
    def test_rejection_form_valid_predefined(self):
        form = RejectionForm(data={
            'predefined_reason': 'Vehicle Not Available',
            'custom_description': ''
        })
        self.assertTrue(form.is_valid())

    def test_rejection_form_invalid_other_no_desc(self):
        form = RejectionForm(data={
            'predefined_reason': 'Other',
            'custom_description': ''
        })
        self.assertFalse(form.is_valid())
        self.assertIn('custom_description', form.errors)

    def test_rejection_form_valid_other_with_desc(self):
        form = RejectionForm(data={
            'predefined_reason': 'Other',
            'custom_description': 'Vehicle broke down on previous trip.'
        })
        self.assertTrue(form.is_valid())

from rentals.forms import CancelModifyForm

class CancelModifyFormTests(TestCase):
    def test_cancel_modify_date_wrong_valid(self):
        today = timezone.localdate()
        form = CancelModifyForm(data={
            'reason': 'Date selection wrong',
            'new_start_date': today + timedelta(days=5),
            'new_end_date': today + timedelta(days=7)
        })
        self.assertTrue(form.is_valid())

    def test_cancel_modify_date_wrong_invalid(self):
        today = timezone.localdate()
        form = CancelModifyForm(data={
            'reason': 'Date selection wrong',
            'new_start_date': today - timedelta(days=1), # Past date
            'new_end_date': today + timedelta(days=7)
        })
        self.assertFalse(form.is_valid())
        self.assertIn('new_start_date', form.errors)

    def test_cancel_modify_other_missing_reason(self):
        form = CancelModifyForm(data={
            'reason': 'Other',
            'custom_reason': ''
        })
        self.assertFalse(form.is_valid())
        self.assertIn('custom_reason', form.errors)

class MultiVehicleBookingTests(TestCase):
    def setUp(self):
        self.vehicle = Vehicle.objects.create(
            name="Yamaha R15",
            vehicle_type="bike",
            price_per_day=1500.00,
            image_path="r15.png",
            description="Track bike."
        )
        self.user = User.objects.create_user(username="testuser", password="testpassword")

    def test_booking_form_quantity_valid(self):
        today = timezone.localdate()
        form_data = {
            'start_date': today + timedelta(days=1),
            'end_date': today + timedelta(days=3),
            'start_time': '10:00',
            'end_time': '18:00',
            'quantity': 3,
            'customer_name': 'Johnathan Doe Smith',
            'customer_age': 25,
            'customer_gender': 'Male',
            'customer_phone': '9876543210',
            'customer_address': '123 Cyberpunk Boulevard, Glassmorphism City, Sector 9',
        }
        mock_file = SimpleUploadedFile("id_proof.png", b"file_content", content_type="image/png")
        form = BookingDetailsForm(data=form_data, files={'id_proof': mock_file})
        self.assertTrue(form.is_valid(), form.errors.as_data())

    def test_booking_form_quantity_invalid_too_high(self):
        today = timezone.localdate()
        form_data = {
            'start_date': today + timedelta(days=1),
            'end_date': today + timedelta(days=3),
            'start_time': '10:00',
            'end_time': '18:00',
            'quantity': 6,  # Max is 5 (invalid)
            'customer_name': 'Johnathan Doe Smith',
            'customer_age': 25,
            'customer_gender': 'Male',
            'customer_phone': '9876543210',
            'customer_address': '123 Cyberpunk Boulevard, Glassmorphism City, Sector 9',
        }
        mock_file = SimpleUploadedFile("id_proof.png", b"file_content", content_type="image/png")
        form = BookingDetailsForm(data=form_data, files={'id_proof': mock_file})
        self.assertFalse(form.is_valid())
        self.assertIn('quantity', form.errors)

    def test_booking_financial_calculation_with_quantity(self):
        # Create a booking with quantity = 3 and duration = 2 days (start to end is 2 days)
        today = timezone.localdate()
        booking = Booking.objects.create(
            user=self.user,
            vehicle=self.vehicle,
            start_date=today + timedelta(days=1),
            end_date=today + timedelta(days=3),
            start_time='10:00',
            end_time='18:00',
            num_days=2,
            quantity=3,
            customer_name='Johnathan Doe Smith',
            customer_age=25,
            customer_gender='Male',
            customer_phone='9876543210',
            customer_address='123 Cyberpunk Boulevard, Glassmorphism City, Sector 9',
            base_amount=0,  # will calculate
            total_amount=0
        )
        
        # Simulate base_amount calculation: num_days (2) * price_per_day (1500) * quantity (3) = 9000
        booking.base_amount = booking.num_days * self.vehicle.price_per_day * booking.quantity
        booking.total_amount = booking.base_amount
        booking.save()
        
        self.assertEqual(booking.base_amount, 9000.00)
        self.assertEqual(booking.total_amount, 9000.00)

class CartTests(TestCase):
    def setUp(self):
        self.vehicle1 = Vehicle.objects.create(
            name="Tesla Model X",
            vehicle_type="car",
            price_per_day=4500.00,
            image_path="tesla_sedan.png",
            description="Luxury SUV."
        )
        self.vehicle2 = Vehicle.objects.create(
            name="KTM Duke 390",
            vehicle_type="bike",
            price_per_day=1500.00,
            image_path="ktm_390.png",
            description="Naked street bike."
        )
        self.user = User.objects.create_user(username="testcartuser", password="testpassword")
        self.client.login(username="testcartuser", password="testpassword")
        session = self.client.session
        session['location_verified'] = True
        session.save()

    def test_cart_operations_and_checkout(self):
        today = timezone.localdate()
        
        # 1. Create two cart items (payment_status='Pending')
        booking1 = Booking.objects.create(
            user=self.user,
            vehicle=self.vehicle1,
            start_date=today + timedelta(days=1),
            end_date=today + timedelta(days=3),
            start_time='10:00',
            end_time='18:00',
            num_days=2,
            quantity=1,
            customer_name='Johnathan Doe Smith',
            customer_age=25,
            customer_gender='Male',
            customer_phone='9876543210',
            customer_address='123 Cyberpunk Boulevard, Glassmorphism City, Sector 9',
            base_amount=9000.00,
            total_amount=9000.00,
            payment_status='Pending'
        )
        
        booking2 = Booking.objects.create(
            user=self.user,
            vehicle=self.vehicle2,
            start_date=today + timedelta(days=1),
            end_date=today + timedelta(days=2),
            start_time='10:00',
            end_time='18:00',
            num_days=1,
            quantity=2,
            customer_name='Johnathan Doe Smith',
            customer_age=25,
            customer_gender='Male',
            customer_phone='9876543210',
            customer_address='123 Cyberpunk Boulevard, Glassmorphism City, Sector 9',
            base_amount=3000.00,
            total_amount=3000.00,
            payment_status='Pending'
        )
        
        # 2. Check context processor count
        from rentals.context_processors import cart_count
        # Mock request with user
        class MockRequest:
            def __init__(self, user):
                self.user = user
        request = MockRequest(self.user)
        self.assertEqual(cart_count(request)['cart_count'], 2)
        
        # 3. View the Cart
        response = self.client.get('/booking/cart/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tesla Model X")
        self.assertContains(response, "KTM Duke 390")
        self.assertContains(response, "12000") # Grand subtotal (9000 + 3000)
        
        # 4. Remove an item
        response = self.client.get(f'/booking/cart/remove/{booking2.id}/')
        self.assertRedirects(response, '/booking/cart/')
        self.assertEqual(Booking.objects.filter(user=self.user, payment_status='Pending').count(), 1)
        
        # 5. Check checkout receipt
        response = self.client.get('/booking/receipt/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tesla Model X")
        self.assertNotContains(response, "KTM Duke 390")
        
        # 6. Process checkout payment
        response = self.client.post('/booking/payment/', {
            'payment_method': 'UPI',
            'upi_id': 'test@upi',
            'utr_id': '123456789012',
        })
        self.assertRedirects(response, '/booking/payment-gateway/')
        
        # 7. Complete checkout success
        response = self.client.get('/booking/payment-success/')
        self.assertEqual(response.status_code, 200)
        
        # Verify bookings are now completed
        self.assertEqual(Booking.objects.filter(user=self.user, payment_status='Completed').count(), 1)
        self.assertEqual(Booking.objects.filter(user=self.user, payment_status='Pending').count(), 0)

    def test_remove_selected_vehicle(self):
        # 1. Setup selected_vehicles in session
        session = self.client.session
        session['selected_vehicles'] = {
            str(self.vehicle1.id): 1,
            str(self.vehicle2.id): 2,
        }
        session.save()

        # 2. Call remove endpoint for vehicle1
        response = self.client.get(f'/booking/details/remove/{self.vehicle1.id}/')
        
        # 3. Assert redirects back to the booking details page since vehicle2 is still selected
        self.assertRedirects(response, '/booking/details/')
        
        # 4. Check session selections
        session = self.client.session
        self.assertNotIn(str(self.vehicle1.id), session['selected_vehicles'])
        self.assertEqual(session['selected_vehicles'][str(self.vehicle2.id)], 2)

        # 5. Remove vehicle2
        response = self.client.get(f'/booking/details/remove/{self.vehicle2.id}/')
        
        # 6. Assert redirects back to select type since no selections are left
        self.assertRedirects(response, '/booking/select-type/')
        
        session = self.client.session
        self.assertEqual(session['selected_vehicles'], {})

class GeolocationAccessTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testcust", password="testpassword")
        self.staff_user = User.objects.create_user(username="adminuser", password="testpassword", is_staff=True)
        self.vehicle = Vehicle.objects.create(
            name="Tesla Model X",
            vehicle_type="car",
            price_per_day=4500.00,
            image_path="tesla_sedan.png",
            description="Luxury SUV."
        )

    def test_verify_location_endpoint_sets_session(self):
        self.client.login(username="testcust", password="testpassword")
        response = self.client.post('/booking/verify-location/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'success'})
        # Reload session to ensure it's persisted
        session = self.client.session
        self.assertTrue(session.get('location_verified'))

    def test_wizard_blocked_without_verification(self):
        self.client.login(username="testcust", password="testpassword")
        response = self.client.get('/booking/select-type/')
        self.assertRedirects(response, '/')
        
        # Verify warning message using django messages framework
        from django.contrib.messages import get_messages
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("verify your location" in str(m) for m in messages))

    def test_wizard_allowed_with_verification(self):
        self.client.login(username="testcust", password="testpassword")
        
        # Verify location
        response = self.client.post('/booking/verify-location/')
        self.assertEqual(response.status_code, 200)
        
        # Try select-type again
        response = self.client.get('/booking/select-type/')
        self.assertEqual(response.status_code, 200)

    def test_staff_exempt_from_location_verification(self):
        self.client.login(username="adminuser", password="testpassword")
        # Admin does not get blocked from select-type
        response = self.client.get('/booking/select-type/')
        self.assertEqual(response.status_code, 200)


from rentals.forms import PaymentForm

class MultiVehiclePrepaymentTests(TestCase):
    def setUp(self):
        self.vehicle1 = Vehicle.objects.create(
            name="Tesla Model X",
            vehicle_type="car",
            price_per_day=4000.00,
            image_path="tesla.png",
            description="Luxury SUV."
        )
        self.vehicle2 = Vehicle.objects.create(
            name="Yamaha R15",
            vehicle_type="bike",
            price_per_day=1000.00,
            image_path="r15.png",
            description="Sport bike."
        )
        self.user = User.objects.create_user(username="prepayuser", password="testpassword")
        self.client.login(username="prepayuser", password="testpassword")
        session = self.client.session
        session['location_verified'] = True
        session.save()

    def test_payment_form_validation_for_multi_vehicle(self):
        # 1 vehicle: Pay on Visit should be valid
        form1 = PaymentForm(data={'payment_method': 'Pay on Visit'}, total_vehicles=1)
        self.assertTrue(form1.is_valid(), form1.errors.as_data())

        # 2 vehicles: Pay on Visit should be invalid
        form2 = PaymentForm(data={'payment_method': 'Pay on Visit'}, total_vehicles=2)
        self.assertFalse(form2.is_valid())
        self.assertIn('payment_method', form2.errors)

        # 2 vehicles: UPI with 25% prepayment choice should be valid
        form3 = PaymentForm(data={
            'payment_method': 'UPI',
            'upi_id': 'test@upi',
            'utr_id': '123456789012',
            'payment_amount_choice': '25'
        }, total_vehicles=2)
        self.assertTrue(form3.is_valid(), form3.errors.as_data())

    def test_prepayment_calculation_25_percent(self):
        today = timezone.localdate()
        booking1 = Booking.objects.create(
            user=self.user,
            vehicle=self.vehicle1,
            start_date=today + timedelta(days=1),
            end_date=today + timedelta(days=2),
            start_time='10:00',
            end_time='18:00',
            num_days=1,
            quantity=1,
            customer_name='Johnathan Doe Smith',
            customer_age=25,
            customer_gender='Male',
            customer_phone='9876543210',
            customer_address='123 Cyberpunk Boulevard, Glassmorphism City, Sector 9',
            base_amount=4000.00,
            total_amount=4000.00,
            payment_status='Pending'
        )
        booking2 = Booking.objects.create(
            user=self.user,
            vehicle=self.vehicle2,
            start_date=today + timedelta(days=1),
            end_date=today + timedelta(days=2),
            start_time='10:00',
            end_time='18:00',
            num_days=1,
            quantity=1,
            customer_name='Johnathan Doe Smith',
            customer_age=25,
            customer_gender='Male',
            customer_phone='9876543210',
            customer_address='123 Cyberpunk Boulevard, Glassmorphism City, Sector 9',
            base_amount=1000.00,
            total_amount=1000.00,
            payment_status='Pending'
        )

        # Total vehicles is 2
        response = self.client.post('/booking/payment/', {
            'payment_method': 'UPI',
            'upi_id': 'test@upi',
            'utr_id': '123456789012',
            'payment_amount_choice': '25'
        })
        self.assertRedirects(response, '/booking/payment-gateway/')

        # Complete checkout
        response = self.client.get('/booking/payment-success/')
        self.assertEqual(response.status_code, 200)

        # Reload bookings
        booking1.refresh_from_db()
        booking2.refresh_from_db()

        # Check prepaid_amount and balance_amount
        self.assertEqual(booking1.prepaid_amount, 1000.00) # 4000 * 0.25
        self.assertEqual(booking1.balance_amount, 3000.00) # 4000 * 0.75
        self.assertEqual(booking2.prepaid_amount, 250.00)  # 1000 * 0.25
        self.assertEqual(booking2.balance_amount, 750.00)  # 1000 * 0.75


class DashboardUndoDeleteTests(TestCase):
    def setUp(self):
        self.vehicle = Vehicle.objects.create(
            name="Tesla Model X",
            vehicle_type="car",
            price_per_day=4500.00,
            image_path="tesla.png",
            description="Luxury SUV."
        )
        self.user = User.objects.create_user(username="undouser", password="testpassword")
        self.client.login(username="undouser", password="testpassword")
        session = self.client.session
        session['location_verified'] = True
        session.save()

        # Create a cancelled booking (which can be deleted from dashboard)
        today = timezone.localdate()
        self.booking = Booking.objects.create(
            user=self.user,
            vehicle=self.vehicle,
            start_date=today + timedelta(days=1),
            end_date=today + timedelta(days=2),
            start_time='10:00',
            end_time='18:00',
            num_days=1,
            quantity=1,
            customer_name='Johnathan Doe Smith',
            customer_age=25,
            customer_gender='Male',
            customer_phone='9876543210',
            customer_address='123 Cyberpunk Boulevard, Glassmorphism City, Sector 9',
            base_amount=4500.00,
            total_amount=4500.00,
            payment_status='Completed',
            status='Cancelled'
        )

    def test_soft_delete_and_undo_flow(self):
        # 1. Booking is visible on home initially
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tesla Model X")
        self.assertNotContains(response, "Booking(s) removed from your dashboard.")

        # 2. Delete the booking (should soft-delete)
        response = self.client.get(f'/booking/delete/{self.booking.id}/')
        self.assertRedirects(response, '/')

        # 3. Verify it is now hidden, and the undo banner is present
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Tesla Model X")
        self.assertContains(response, "Booking(s) removed from your dashboard.")
        self.assertContains(response, "/booking/undo-delete/")
        
        # 4. Perform Undo
        response = self.client.get('/booking/undo-delete/')
        self.assertRedirects(response, '/')

        # 5. Verify it is restored and banner is gone
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tesla Model X")
        self.assertNotContains(response, "Booking(s) removed from your dashboard.")

    def test_dismiss_delete_flow(self):
        # 1. Delete booking
        self.client.get(f'/booking/delete/{self.booking.id}/')

        # 2. Verify banner is present
        response = self.client.get('/')
        self.assertContains(response, "Booking(s) removed from your dashboard.")

        # 3. Dismiss the deletion
        response = self.client.get('/booking/dismiss-delete/')
        self.assertRedirects(response, '/')

        # 4. Verify banner is gone and booking is still hidden
        response = self.client.get('/')
        self.assertNotContains(response, "Booking(s) removed from your dashboard.")
        self.assertNotContains(response, "Tesla Model X")


class VehicleAvailabilityTests(TestCase):
    def setUp(self):
        self.vehicle = Vehicle.objects.create(
            name="Tesla Model S",
            vehicle_type="car",
            price_per_day=5000.00,
            image_path="tesla.png",
            description="Premium sports car."
        )
        self.user = User.objects.create_user(username="availuser", password="testpassword")
        self.client.login(username="availuser", password="testpassword")
        session = self.client.session
        session['location_verified'] = True
        session.save()

    def test_select_model_initializes_availability(self):
        session = self.client.session
        session['booking_vehicle_type'] = 'car'
        session.save()
        
        response = self.client.get('/booking/select-model/')
        self.assertEqual(response.status_code, 200)
        
        # Verify availability is set in the session
        session = self.client.session
        self.assertIn('vehicle_availabilities', session)
        avail = session['vehicle_availabilities'].get(str(self.vehicle.id))
        self.assertTrue(2 <= avail <= 5)

    def test_select_model_caps_quantity_at_availability(self):
        session = self.client.session
        session['booking_vehicle_type'] = 'car'
        # Set availability to 2 in session
        session['vehicle_availabilities'] = {str(self.vehicle.id): 2}
        session.save()
        
        # Post quantity 4, which is greater than availability 2
        response = self.client.post('/booking/select-model/', {
            f'qty_{self.vehicle.id}': 4,
            'action': 'proceed'
        })
        self.assertRedirects(response, '/booking/details/')
        
        # Verify it was capped at 2
        session = self.client.session
        self.assertEqual(session['selected_vehicles'].get(str(self.vehicle.id)), 2)




