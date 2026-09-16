from decimal import Decimal, InvalidOperation
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from apps.cart.forms import AddCartForm
from .models import Category, MenuItem


def home(request):
    return render(request, 'home.html', {'featured': MenuItem.objects.select_related('category').filter(
        is_featured=True, is_available=True, category__is_active=True, available_date__lte=timezone.localdate())[:4],
        'categories': Category.objects.filter(is_active=True)})


def about(request):
    return render(request, 'about.html')


def menu_list(request):
    items = MenuItem.objects.select_related('category').filter(category__is_active=True)
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', '')
    if query:
        items = items.filter(Q(name__icontains=query) | Q(description__icontains=query) | Q(category__name__icontains=query))
    if category:
        items = items.filter(category__slug=category)
    available = Q(is_available=True, stock__gt=0, available_date__lte=timezone.localdate())
    if request.GET.get('availability') == 'available':
        items = items.filter(available)
    elif request.GET.get('availability') == 'unavailable':
        items = items.exclude(available)
    price_error = ''
    for key, lookup in [('min_price', 'price__gte'), ('max_price', 'price__lte')]:
        value = request.GET.get(key, '')
        if value:
            try:
                price = Decimal(value)
                if not price.is_finite() or price < 0 or price > 99999999:
                    raise InvalidOperation
                items = items.filter(**{lookup: price})
            except InvalidOperation:
                price_error = 'Enter a valid non-negative price.'
    ordering = {'newest': '-created_at', 'price_low': 'price', 'price_high': '-price', 'name': 'name'}
    items = items.order_by(ordering.get(request.GET.get('sort'), 'id'), 'pk')
    return render(request, 'menu/list.html', {'page_obj': Paginator(items, 12).get_page(request.GET.get('page')),
        'categories': Category.objects.filter(is_active=True), 'query': query, 'category_slug': category, 'price_error': price_error})


def menu_detail(request, slug):
    item = get_object_or_404(MenuItem.objects.select_related('category'), slug=slug, category__is_active=True)
    return render(request, 'menu/detail.html', {'item': item, 'form': AddCartForm(item=item)})
