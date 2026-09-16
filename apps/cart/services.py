from django.db import transaction
from django.db.models import Sum
from .models import Cart, CartItem


def get_cart(request, create=True):
    if request.user.is_authenticated:
        lookup = {'user': request.user}
    else:
        if not request.session.session_key:
            if not create:
                return None
            request.session.create()
        lookup = {'session_key': request.session.session_key}
    if create:
        return Cart.objects.get_or_create(**lookup)[0]
    return Cart.objects.filter(**lookup).first()


@transaction.atomic
def merge_guest_cart(user, session_key):
    if not session_key:
        return
    guest = Cart.objects.filter(session_key=session_key, user__isnull=True).first()
    if not guest:
        return
    target, _ = Cart.objects.get_or_create(user=user)
    for line in guest.items.all():
        item, created = target.items.get_or_create(menu_item=line.menu_item, size=line.size,
            temperature=line.temperature, sweetness=line.sweetness, defaults={'quantity': line.quantity})
        if not created:
            item.quantity += line.quantity
            item.save(update_fields=['quantity'])
    guest.delete()


def add_item(cart, menu_item, data):
    if not menu_item.can_order:
        raise ValueError('This item is currently unavailable.')
    quantity = data['quantity']
    current = cart.items.filter(menu_item=menu_item).aggregate(n=Sum('quantity'))['n'] or 0
    if current + quantity > menu_item.stock:
        raise ValueError(f'Only {menu_item.stock} available. Your cart already contains {current}.')
    line, created = CartItem.objects.get_or_create(cart=cart, menu_item=menu_item,
        size=data.get('size', ''), temperature=data.get('temperature', ''), sweetness=data.get('sweetness', ''),
        defaults={'quantity': quantity})
    if not created:
        line.quantity += quantity
        line.save(update_fields=['quantity'])
