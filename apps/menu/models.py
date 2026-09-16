from decimal import Decimal
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, FileExtensionValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.text import slugify
from django.conf import settings


def validate_image(value):
    # Validate new uploads. Existing files need not be reopened during unrelated edits.
    if getattr(value, '_committed', False):
        return
    if value.size > 5 * 1024 * 1024:
        raise ValidationError('Image must be 5 MB or smaller.')


IMAGE_VALIDATORS = [FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp']), validate_image]


def unique_slug(instance):
    base = slugify(instance.name) or 'item'
    slug, index = base, 2
    while type(instance).objects.filter(slug=slug).exclude(pk=instance.pk).exists():
        slug = f'{base}-{index}'
        index += 1
    return slug


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, max_length=140, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', validators=IMAGE_VALIDATORS, default='menu/placeholder.jpg')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['id']
        verbose_name_plural = 'Categories'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self)
        if not self.image or self.image.name == 'menu/placeholder.jpg':
            from .placeholders import make_placeholder
            self.image = f'categories/{self.slug}.jpg'
            make_placeholder(settings.MEDIA_ROOT / self.image.name, self.name, self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class MenuItem(models.Model):
    class Type(models.TextChoices):
        COFFEE = 'coffee', 'Coffee'
        NON_COFFEE = 'non-coffee', 'Non-Coffee'
        TEA = 'tea', 'Tea'
        BAKERY = 'bakery', 'Bakery'
        DESSERT = 'dessert', 'Dessert'
        FOOD = 'food', 'Food'

    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='menu_items')
    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True, max_length=180, blank=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0'))])
    stock = models.PositiveIntegerField(default=20)
    image = models.ImageField(upload_to='menu/', validators=IMAGE_VALIDATORS, default='menu/placeholder.jpg')
    menu_type = models.CharField(max_length=15, choices=Type.choices, default=Type.COFFEE)
    available_sizes = models.JSONField(default=list, blank=True)
    temperature_option = models.CharField(max_length=5, choices=[('hot', 'Hot'), ('iced', 'Iced'), ('both', 'Both')], default='both')
    is_available = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    available_date = models.DateField(default=timezone.localdate)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['id']
        constraints = [models.CheckConstraint(condition=Q(price__gte=0), name='menu_price_nonnegative')]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self)
        if not self.image or self.image.name == 'menu/placeholder.jpg':
            from .placeholders import make_placeholder
            self.image = f'menu/{self.slug}.jpg'
            make_placeholder(settings.MEDIA_ROOT / self.image.name, self.name, self.get_menu_type_display())
        super().save(*args, **kwargs)

    @property
    def is_drink(self):
        return self.menu_type in ('coffee', 'non-coffee', 'tea')

    @property
    def can_order(self):
        return self.is_available and self.stock > 0 and self.category.is_active and self.available_date <= timezone.localdate()

    @property
    def temperatures(self):
        return ['Hot', 'Iced'] if self.temperature_option == 'both' else [self.temperature_option.title()]

    def __str__(self):
        return self.name
