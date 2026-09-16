from django.db.models import Sum
from .services import get_cart


def cart_count(request):
    cart = get_cart(request, create=False)
    count = (cart.items.aggregate(n=Sum('quantity'))['n'] or 0) if cart else 0
    return {'cart_count': count}
