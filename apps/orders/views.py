import uuid
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import OperationalError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from apps.cart.services import get_cart
from .forms import CheckoutForm
from .models import LoyaltyAccount, Order
from .services import place_order
from .services import normalize_phone


@login_required
def checkout(request):
    cart = get_cart(request, create=False)
    if request.method == 'GET' and (not cart or not cart.items.exists()):
        return redirect('cart')
    if 'checkout_token' not in request.session:
        request.session['checkout_token'] = str(uuid.uuid4())
    loyalty_account = LoyaltyAccount.objects.filter(orders__user=request.user).order_by('-orders__created_at').first()
    form = CheckoutForm(request.POST or None, cart=cart, loyalty_account=loyalty_account,
        initial={'full_name': request.user.get_full_name(), 'order_type': 'take_away',
                 'checkout_token': request.session['checkout_token']})
    if request.method == 'POST' and form.is_valid():
        token = str(form.cleaned_data['checkout_token'])
        existing = Order.objects.filter(checkout_token=token, user=request.user).first()
        if existing:
            return redirect('order_success', pk=existing.pk)
        if token != request.session['checkout_token']:
            form.add_error(None, 'This checkout expired. Reload the page and try again.')
        else:
            try:
                order = place_order(request.user, cart, form.cleaned_data, form.cleaned_data.get('reward_line'))
                request.session['checkout_token'] = str(uuid.uuid4())
                return redirect('order_success', pk=order.pk)
            except ValueError as exc:
                form.add_error(None, str(exc))
            except OperationalError:
                form.add_error(None, 'The shop is busy. Your order was not submitted; please try again.')
    return render(request, 'orders/checkout.html', {'form': form, 'cart': cart,
        'items': cart.items.select_related('menu_item') if cart else [], 'loyalty_account': loyalty_account})


@login_required
@require_POST
def loyalty_status(request):
    phone = normalize_phone(request.POST.get('phone', ''))
    account = LoyaltyAccount.objects.filter(phone=phone).first() if 8 <= len(phone) <= 15 else None
    return JsonResponse({
        'eligible': bool(account and account.reward_balance),
        'reward_balance': account.reward_balance if account else 0,
        'visits_remaining': account.visits_to_next_reward if account else 10,
    })


@login_required
def order_list(request):
    orders = request.user.orders.prefetch_related('items')
    return render(request, 'orders/list.html', {'page_obj': Paginator(orders, 10).get_page(request.GET.get('page'))})


@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order.objects.prefetch_related('items'), pk=pk, user=request.user)
    return render(request, 'orders/detail.html', {'order': order})


@login_required
def order_status(request, pk):
    order = get_object_or_404(Order.objects.select_related('loyalty_account'), pk=pk, user=request.user)
    messages = {
        'pending': 'WE RECEIVED YOUR ORDER',
        'preparing': 'BREWING YOUR ORDER',
        'ready': 'READY FOR PICKUP',
        'completed': 'ORDER COMPLETE',
        'cancelled': 'ORDER CANCELLED',
    }
    loyalty = None
    if order.loyalty_account:
        loyalty = {'completed_purchases': order.loyalty_account.completed_purchases,
                   'reward_balance': order.loyalty_account.reward_balance}
    response = JsonResponse({'status': order.status, 'display': order.get_status_display(),
        'message': messages[order.status], 'updated_at': order.updated_at.isoformat(), 'loyalty': loyalty})
    response['Cache-Control'] = 'no-store'
    return response


@login_required
def order_success(request, pk):
    return render(request, 'orders/success.html', {'order': get_object_or_404(Order, pk=pk, user=request.user)})
