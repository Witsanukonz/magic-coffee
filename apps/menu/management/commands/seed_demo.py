import os
import shutil
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from apps.accounts.models import User
from apps.menu.models import Category, MenuItem
from apps.menu.demo_data import DEMO_MENU
from apps.menu.placeholders import make_placeholder


class Command(BaseCommand):
    help = 'Create 6 categories, 28 illustrated menus and two local demo accounts. Safe to repeat.'

    def handle(self, *args, **options):
        make_placeholder(settings.MEDIA_ROOT / 'menu/placeholder.jpg', 'Freshly made', 'Coffee')
        for name, category_name, price, description in DEMO_MENU:
            slug = slugify(name)
            image_name = f'menu/{slug}.jpg'
            image_path = settings.MEDIA_ROOT / image_name
            photo_path = settings.BASE_DIR / 'static/images/menu' / f'{slug}.jpg'
            if photo_path.exists() and not image_path.exists():
                image_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(photo_path, image_path)
            else:
                make_placeholder(image_path, name, category_name)
            category, _ = Category.objects.get_or_create(slug=slugify(category_name), defaults={
                'name': category_name, 'description': f'Everyday favorites from our {category_name.lower()} collection.',
                'image': image_name})
            menu_type = 'food' if category_name == 'Breakfast' else slugify(category_name)
            is_drink = category_name in ['Coffee', 'Non-Coffee', 'Tea']
            MenuItem.objects.get_or_create(slug=slug, defaults={
                'name': name, 'category': category, 'description': description, 'price': price,
                'stock': 4 if name in ['Cold Brew', 'Butter Croissant', 'Basque Cheesecake'] else 25,
                'menu_type': menu_type, 'image': image_name, 'available_sizes': ['Small','Medium','Large'] if is_drink else [],
                'temperature_option': 'iced' if 'Iced' in name or name in ['Cold Brew','Dirty Coffee'] else 'both',
                'is_featured': name in ['Cafe Latte','Iced Latte','Butter Croissant','Basque Cheesecake'],
            })
        for username, role, first_name in [('demo_admin','admin','Admin'),('demo_customer','customer','Coffee Lover')]:
            if not User.objects.filter(username=username).exists():
                password = os.environ.get(f'MAGIC_{role.upper()}_PASSWORD', 'MagicDemo!2026')
                User.objects.create_user(username=username, email=f'{username}@example.com', password=password,
                                         role=role, first_name=first_name)
        self.stdout.write(self.style.SUCCESS('Demo ready: 6 categories, 28 menu items, demo_admin and demo_customer.'))
        self.stdout.write('Existing records and passwords were preserved. See README for local demo login instructions.')
