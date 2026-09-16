from collections import Counter
from decimal import Decimal
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from apps.menu.models import MenuItem
from .models import LoyaltyAccount, Order, OrderItem


def normalize_phone(phone):
    return ''.join(char for char in phone if char.isdigit())


def _locked_loyalty_account(phone):
    normalized = normalize_phone(phone)
    account, _ = LoyaltyAccount.objects.get_or_create(phone=normalized)
    return LoyaltyAccount.objects.select_for_update().get(pk=account.pk)


@transaction.atomic
def place_order(user, cart, data, reward_line_id=None):
    existing = Order.objects.filter(checkout_token=data['checkout_token'], user=user).first()
    if existing:
        return existing
    lines = list(cart.items.select_related('menu_item__category')) if cart else []
    if not lines:
        raise ValueError('Your cart is empty.')
    quantities = Counter()
    total = Decimal('0.00')
    for line in lines:
        item = line.menu_item
        if not item.can_order or line.quantity < 1:
            raise ValueError(f'{item.name} is no longer available. Please update your cart.')
        if item.is_drink and (line.size not in item.available_sizes or line.temperature not in item.temperatures
                              or line.sweetness not in ['0', '25', '50', '75', '100']):
            raise ValueError(f'Options for {item.name} have changed. Remove it and choose again.')
        quantities[item.pk] += line.quantity
        total += line.subtotal
    reward_line = None
    if reward_line_id:
        reward_line = next((line for line in lines if str(line.pk) == str(reward_line_id)), None)
        if not reward_line or reward_line.menu_item.menu_type != 'coffee':
            raise ValueError('Choose a coffee in your order to use a free coffee reward.')
    loyalty_account = _locked_loyalty_account(data['phone'])
    discount = Decimal('0.00')
    if reward_line:
        if loyalty_account.reward_balance < 1:
            raise ValueError('No free coffee reward is available for this phone number.')
        discount = reward_line.menu_item.price
        loyalty_account.reward_balance -= 1
        loyalty_account.save(update_fields=['reward_balance', 'updated_at'])
    # Conditional database updates prevent overselling, including multiple options of the same menu.
    for item_id, quantity in sorted(quantities.items()):
        changed = MenuItem.objects.filter(pk=item_id, stock__gte=quantity, is_available=True,
            category__is_active=True, available_date__lte=timezone.localdate()).update(stock=F('stock') - quantity)
        if not changed:
            raise ValueError('Stock changed while ordering. Please review your cart and try again.')
    order = Order.objects.create(user=user, loyalty_account=loyalty_account, total_price=total - discount,
        loyalty_discount=discount, loyalty_reward_item_name=reward_line.menu_item.name if reward_line else '',
        loyalty_reward_redeemed=bool(reward_line), **{k: data[k] for k in
        ['full_name', 'phone', 'order_type', 'note', 'checkout_token']})
    order.order_number = f'MC{order.pk:05d}'
    order.save(update_fields=['order_number'])
    OrderItem.objects.bulk_create([OrderItem(order=order, menu_item=line.menu_item, menu_name=line.menu_item.name,
        price=line.menu_item.price, quantity=line.quantity, size=line.size, temperature=line.temperature,
        sweetness=line.sweetness, subtotal=line.subtotal) for line in lines])
    cart.items.all().delete()
    return order


TRANSITIONS = {'pending': ['preparing', 'cancelled'], 'preparing': ['ready', 'cancelled'],
               'ready': ['completed', 'cancelled'], 'completed': [], 'cancelled': []}


@transaction.atomic
def change_status(order_id, status):
    order = Order.objects.select_for_update().get(pk=order_id)
    if status == order.status:
        return order
    if status not in TRANSITIONS[order.status]:
        raise ValueError('This status change is not allowed. Follow Pending → Preparing → Ready → Completed.')
    previous = order.status
    changed = Order.objects.filter(pk=order.pk, status=previous).update(status=status, updated_at=timezone.now())
    if not changed:
        raise ValueError('Another admin updated this order. Refresh and try again.')
    if status == 'cancelled':
        for line in order.items.exclude(menu_item=None):
            MenuItem.objects.filter(pk=line.menu_item_id).update(stock=F('stock') + line.quantity)
        if order.loyalty_reward_redeemed and order.loyalty_account_id:
            account = LoyaltyAccount.objects.select_for_update().get(pk=order.loyalty_account_id)
            account.reward_balance += 1
            account.save(update_fields=['reward_balance', 'updated_at'])
    if status == 'completed' and order.loyalty_account_id and not order.loyalty_awarded:
        if order.loyalty_reward_redeemed:
            Order.objects.filter(pk=order.pk, loyalty_awarded=False).update(loyalty_awarded=True)
        else:
            account = LoyaltyAccount.objects.select_for_update().get(pk=order.loyalty_account_id)
            account.completed_purchases += 1
            if account.completed_purchases % 10 == 0:
                account.reward_balance += 1
            account.save(update_fields=['completed_purchases', 'reward_balance', 'updated_at'])
            Order.objects.filter(pk=order.pk, loyalty_awarded=False).update(loyalty_awarded=True)
    order.status = status
    return order
