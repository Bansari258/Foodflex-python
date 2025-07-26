from vendor.models import Order

def cart_count(request):
    if request.user.is_authenticated:
        ongoing_orders = Order.objects.filter(user=request.user, status='ongoing').order_by('-created_at')
        cart_count = 0
        vendor_id = None

        if ongoing_orders.exists():
            most_recent_order = ongoing_orders.first()
            vendor_id = most_recent_order.vendor.id
            for order in ongoing_orders:
                for item_id, details in order.order_items.items():
                    cart_count += details.get('qty', 0)

        return {
            'cart_count': cart_count,
            'cart_vendor_id': vendor_id,
        }
    return {
        'cart_count': 0,
        'cart_vendor_id': None,
    }