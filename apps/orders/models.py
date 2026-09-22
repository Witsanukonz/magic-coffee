"""ข้อมูลถาวรของแต้มสะสม, ออเดอร์ และรายการสินค้าในออเดอร์."""

from django.conf import settings
from django.db import models
from django.db.models import Q


class LoyaltyAccount(models.Model):
    """บัญชีแต้มสะสมหนึ่งบัญชีต่อหนึ่งเบอร์โทรศัพท์."""
    phone = models.CharField(max_length=15, unique=True)
    completed_purchases = models.PositiveIntegerField(default=0)
    reward_balance = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['phone']

    @property
    def progress_to_reward(self):
        """จำนวนการซื้อที่สะสมอยู่ในรอบปัจจุบัน (0 ถึง 9)."""
        return self.completed_purchases % 10

    @property
    def visits_to_next_reward(self):
        """จำนวนครั้งที่เหลือก่อนแลกกาแฟฟรีได้อีกครั้ง."""
        return 10 - self.progress_to_reward if self.progress_to_reward else 10

    def __str__(self):
        return f'Loyalty {self.phone}'


class Order(models.Model):
    """หัวออเดอร์: ข้อมูลลูกค้า, ราคา, แต้ม และสถานะการทำเครื่องดื่ม."""
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PREPARING = 'preparing', 'Preparing'
        READY = 'ready', 'Ready'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    order_number = models.CharField(max_length=20, unique=True, null=True, editable=False)
    checkout_token = models.UUIDField(unique=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='orders')
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=25)
    order_type = models.CharField(max_length=10, choices=[('dine_in', 'Dine In'), ('take_away', 'Take Away')])
    note = models.TextField(blank=True, max_length=1000)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    loyalty_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    loyalty_reward_item_name = models.CharField(max_length=150, blank=True)
    loyalty_reward_redeemed = models.BooleanField(default=False)
    loyalty_awarded = models.BooleanField(default=False)
    loyalty_account = models.ForeignKey(LoyaltyAccount, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='orders')
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.order_number or 'New order'


class OrderItem(models.Model):
    """Snapshot ของสินค้าในออเดอร์ เพื่อให้ประวัติไม่เปลี่ยนตามเมนูภายหลัง."""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey('menu.MenuItem', on_delete=models.SET_NULL, null=True)
    menu_name = models.CharField(max_length=150)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    size = models.CharField(max_length=10, blank=True)
    temperature = models.CharField(max_length=10, blank=True)
    sweetness = models.CharField(max_length=5, blank=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(quantity__gt=0), name='order_quantity_positive')]
