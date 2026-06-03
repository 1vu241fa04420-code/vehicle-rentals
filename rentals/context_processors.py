def cart_count(request):
    if request.user.is_authenticated:
        count = request.user.bookings.filter(payment_status='Pending').count()
        return {'cart_count': count}
    return {'cart_count': 0}
