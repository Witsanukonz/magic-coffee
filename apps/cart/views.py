"""Endpoints ของตะกร้าสินค้า: แสดง, เพิ่ม, เปลี่ยนจำนวน และลบรายการ."""

from django.contrib import messages
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from apps.menu.models import MenuItem
from .forms import AddCartForm
from .services import get_cart, add_item


def cart_detail(request):
    """แสดงตะกร้าปัจจุบัน โดยไม่สร้างตะกร้าเปล่าให้ผู้เยี่ยมชม."""
    cart = get_cart(request, create=False)
    return render(request, 'cart/detail.html', {'cart': cart,
        'items': cart.items.select_related('menu_item__category') if cart else []})


@require_POST
def cart_add(request, pk):
    """เพิ่มเมนูเข้าตะกร้าจากหน้ารายละเอียดหรือปุ่ม quick add."""
    item = get_object_or_404(MenuItem.objects.select_related('category'), pk=pk)
    data = request.POST.copy()
    if data.get('quick') == '1':
        data.update(quantity='1', size=next(iter(item.available_sizes), ''), temperature=item.temperatures[0], sweetness='50')
    form = AddCartForm(data, item=item)
    if form.is_valid():
        try:
            add_item(get_cart(request), item, form.cleaned_data)
            messages.success(request, 'Item added to cart.')
            return redirect('cart')
        except ValueError as exc:
            form.add_error(None, str(exc))
    return render(request, 'menu/detail.html', {'item': item, 'form': form}, status=400)


@require_POST
def cart_update(request, pk):
    """แก้จำนวนสินค้าและตอบ JSON เมื่อ JavaScript ขอให้อัปเดตราคาแบบไม่รีเฟรช."""
    cart = get_cart(request)
    line = get_object_or_404(cart.items.select_related('menu_item'), pk=pk)
    try:
        quantity = int(request.POST.get('quantity', ''))
        others = cart.items.filter(menu_item=line.menu_item).exclude(pk=line.pk).aggregate(n=Sum('quantity'))['n'] or 0
        if quantity < 1 or quantity + others > line.menu_item.stock:
            raise ValueError
        line.quantity = quantity
        line.save(update_fields=['quantity'])
        # หน้า cart ใช้ JSON เพื่อเปลี่ยนยอดเงินทันที; form ปกติยัง redirect ได้เหมือนเดิม.
        if request.headers.get('Accept') == 'application/json':
            cart_total = cart.total
            cart_count = cart.items.aggregate(count=Sum('quantity'))['count'] or 0
            return JsonResponse({'quantity': line.quantity, 'line_total': str(line.subtotal),
                                 'cart_total': str(cart_total), 'cart_count': cart_count})
        messages.success(request, 'Cart updated.')
    except (ValueError, OverflowError):
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({'error': 'Quantity must fit available stock.'}, status=400)
        messages.error(request, 'Quantity must be positive and all options together must fit available stock.')
    return redirect('cart')


@require_POST
def cart_remove(request, pk):
    """ลบเพียงรายการที่เลือกออกจากตะกร้าปัจจุบัน."""
    get_object_or_404(get_cart(request).items, pk=pk).delete()
    messages.success(request, 'Item removed from cart.')
    return redirect('cart')
