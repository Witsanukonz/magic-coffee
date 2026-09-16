from functools import wraps
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, ProtectedError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.utils import timezone
from apps.accounts.models import User
from apps.accounts.forms import AdminUserForm
from apps.menu.models import MenuItem, Category
from apps.menu.forms import MenuForm, CategoryForm
from apps.orders.models import Order
from apps.orders.services import change_status, TRANSITIONS


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(request, *args, **kwargs):
        if not request.user.is_admin:
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return wrapped


@admin_required
def overview(request):
    today = timezone.localdate()
    return render(request, 'dashboard/overview.html', {
        'active': 'overview', 'menu_count': MenuItem.objects.count(),
        'customer_count': User.objects.filter(role='customer').count(),
        'order_count': Order.objects.filter(created_at__date=today).count(),
        'pending_count': Order.objects.filter(status__in=['pending', 'preparing']).count(),
        'ready_count': Order.objects.filter(status='ready').count(),
        'available_menu_count': MenuItem.objects.filter(is_available=True, stock__gt=0,
            category__is_active=True, available_date__lte=today).count(),
        'recent_orders': _recent_orders(),
        'low_stock': MenuItem.objects.filter(stock__lte=5).order_by('stock')[:8],
    })


RESOURCES = {
    'menu': (MenuItem, MenuForm, 'Menu'),
    'categories': (Category, CategoryForm, 'Category'),
    'users': (User, AdminUserForm, 'User'),
}


def _recent_orders():
    return Order.objects.select_related('user').annotate(item_count=Sum('items__quantity')).order_by('-created_at', '-pk')[:6]


def _order_board(orders):
    board_orders = list(orders.prefetch_related('items'))
    for order in board_orders:
        allowed = TRANSITIONS[order.status]
        order.next_status = allowed[0] if allowed else ''
    return [{'key': key, 'label': label, 'orders': [order for order in board_orders if order.status == key]}
            for key, label in [('pending', 'NEW'), ('preparing', 'PREPARING'), ('ready', 'READY'), ('completed', 'COMPLETED')]]


@admin_required
def resource_list(request, resource):
    model, _, label = RESOURCES[resource]
    objects = model.objects.all()
    query = request.GET.get('q', '').strip()
    if resource == 'menu':
        objects = objects.select_related('category')
        if query:
            objects = objects.filter(Q(name__icontains=query) | Q(description__icontains=query) | Q(category__name__icontains=query))
        if request.GET.get('category'):
            objects = objects.filter(category__slug=request.GET['category'])
        available = Q(is_available=True, stock__gt=0, category__is_active=True, available_date__lte=timezone.localdate())
        if request.GET.get('status') == 'active':
            objects = objects.filter(available)
        elif request.GET.get('status') == 'inactive':
            objects = objects.exclude(available)
    elif resource == 'users':
        if query:
            objects = objects.filter(Q(username__icontains=query) | Q(email__icontains=query) |
                                     Q(first_name__icontains=query) | Q(last_name__icontains=query))
        if request.GET.get('role') in ['admin', 'customer']:
            objects = objects.filter(role=request.GET['role'])
        if request.GET.get('status') in ['active', 'inactive']:
            objects = objects.filter(is_active=request.GET['status'] == 'active')
    else:
        objects = objects.annotate(menu_count=Count('menu_items'))
        if query:
            objects = objects.filter(Q(name__icontains=query) | Q(description__icontains=query))
    return render(request, 'dashboard/list.html', {'active': resource, 'resource': resource, 'label': label,
        'page_obj': Paginator(objects.order_by('-pk'), 10).get_page(request.GET.get('page')),
        'categories': Category.objects.all(), 'query': query})


@admin_required
def resource_edit(request, resource, pk=None):
    model, form_class, label = RESOURCES[resource]
    obj = get_object_or_404(model, pk=pk) if pk else None
    kwargs = {'actor': request.user} if resource == 'users' else {}
    form = form_class(request.POST or None, request.FILES or None, instance=obj, **kwargs)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'{label} {"updated" if pk else "created"} successfully.')
        return redirect('dashboard_resource', resource=resource)
    return render(request, 'dashboard/form.html', {'active': resource, 'resource': resource, 'label': label,
        'form': form, 'object': obj, 'editing': bool(pk)})


@admin_required
def resource_detail(request, resource, pk):
    model, _, label = RESOURCES[resource]
    obj = get_object_or_404(model, pk=pk)
    return render(request, 'dashboard/detail.html', {'active': resource, 'resource': resource, 'label': label, 'object': obj})


@admin_required
@require_POST
def resource_delete(request, resource, pk):
    model, _, label = RESOURCES[resource]
    obj = get_object_or_404(model, pk=pk)
    if resource == 'users' and obj.pk == request.user.pk:
        messages.error(request, 'You cannot delete your own account.')
    else:
        try:
            obj.delete()
            messages.success(request, f'{label} deleted successfully.')
        except ProtectedError:
            messages.error(request, 'This category contains menu items. Move or delete those items first.')
    return redirect('dashboard_resource', resource=resource)


@admin_required
@require_POST
def user_toggle(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user.pk == request.user.pk:
        messages.error(request, 'You cannot disable your own account.')
    else:
        user.is_active = not user.is_active
        user.save(update_fields=['is_active'])
        messages.success(request, 'User status updated successfully.')
    return redirect('dashboard_resource', resource='users')


@admin_required
def order_list(request):
    orders = Order.objects.select_related('user').annotate(item_count=Sum('items__quantity')).order_by('-created_at', '-pk')
    query = request.GET.get('q', '').strip()
    if query:
        orders = orders.filter(Q(order_number__icontains=query) | Q(full_name__icontains=query) | Q(phone__icontains=query))
    if request.GET.get('status') in Order.Status.values:
        orders = orders.filter(status=request.GET['status'])
    board = _order_board(orders)
    return render(request, 'dashboard/orders.html', {'active': 'orders',
        'page_obj': Paginator(orders, 10).get_page(request.GET.get('page')), 'statuses': Order.Status.choices,
        'query': query, 'board': board})


@admin_required
def live_recent_orders(request):
    response = render(request, 'dashboard/order_table.html', {'orders': _recent_orders()})
    response['Cache-Control'] = 'no-store'
    return response


@admin_required
def live_order_board(request):
    orders = Order.objects.select_related('user').annotate(item_count=Sum('items__quantity')).order_by('-created_at', '-pk')
    response = render(request, 'dashboard/order_board.html', {'board': _order_board(orders)})
    response['Cache-Control'] = 'no-store'
    return response


@admin_required
def live_sidebar_alerts(request):
    alerts = []
    pending_order_count = Order.objects.filter(status='pending').count()
    for item in MenuItem.objects.filter(is_available=True, stock=0).order_by('name')[:3]:
        alerts.append({'id': f'out-{item.pk}', 'kind': 'out', 'title': 'Out of stock',
                       'detail': item.name, 'url': reverse('dashboard_edit', kwargs={'resource': 'menu', 'pk': item.pk})})
    for item in MenuItem.objects.filter(is_available=True, stock__gt=0, stock__lte=5).order_by('stock', 'name')[:3]:
        alerts.append({'id': f'low-{item.pk}', 'kind': 'low', 'title': f'Only {item.stock} left',
                       'detail': item.name, 'url': reverse('dashboard_edit', kwargs={'resource': 'menu', 'pk': item.pk})})
    response = JsonResponse({'alerts': alerts, 'pending_order_count': pending_order_count})
    response['Cache-Control'] = 'no-store'
    return response


@admin_required
def order_detail(request, pk):
    order = get_object_or_404(Order.objects.select_related('user').prefetch_related('items'), pk=pk)
    if request.method == 'POST':
        try:
            change_status(order.pk, request.POST.get('status'))
            messages.success(request, 'Order status updated successfully.')
        except ValueError as exc:
            messages.error(request, str(exc))
        if request.POST.get('from_board') == '1':
            return redirect('dashboard_orders')
        return redirect('dashboard_order', pk=pk)
    allowed = TRANSITIONS[order.status]
    return render(request, 'dashboard/order_detail.html', {'active': 'orders', 'order': order,
        'statuses': [(key, label) for key, label in Order.Status.choices if key in allowed]})


@admin_required
@require_POST
def menu_availability(request, pk):
    item = get_object_or_404(MenuItem, pk=pk)
    item.is_available = not item.is_available
    item.save(update_fields=['is_available', 'updated_at'])
    messages.success(request, f'{item.name} is now {"available" if item.is_available else "sold out"}.')
    return redirect('dashboard_resource', resource='menu')
