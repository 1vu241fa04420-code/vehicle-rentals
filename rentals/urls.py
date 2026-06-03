from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_signup_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Booking Wizard
    path('booking/verify-location/', views.verify_location_view, name='verify_location'),
    path('booking/select-type/', views.select_type, name='select_type'),
    path('booking/select-model/', views.select_model, name='select_model'),
    path('booking/details/', views.booking_details_multi, name='booking_details_multi'),
    path('booking/details/remove/<int:vehicle_id>/', views.remove_selected_vehicle, name='remove_selected_vehicle'),
    path('booking/details/<int:vehicle_id>/', views.booking_details, name='booking_details'),
    path('booking/cart/', views.cart_view, name='cart'),
    path('booking/cart/remove/<int:booking_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('booking/receipt/', views.billing_receipt, name='billing_receipt'),
    path('booking/payment/', views.payment_processing, name='payment_processing'),
    path('booking/payment-gateway/', views.payment_portal, name='payment_portal'),
    path('booking/payment-success/', views.payment_success, name='payment_success'),
    path('booking/reject/<int:booking_id>/', views.reject_booking, name='reject_booking'),
    path('booking/cancel-modify/<int:booking_id>/', views.cancel_modify_booking, name='cancel_modify_booking'),
    path('booking/delete/<int:booking_id>/', views.delete_booking, name='delete_booking'),
    path('booking/delete-all/', views.delete_all_bookings, name='delete_all_bookings'),
    path('booking/undo-delete/', views.undo_delete_booking, name='undo_delete_booking'),
    path('booking/dismiss-delete/', views.dismiss_delete_booking, name='dismiss_delete_booking'),
]
