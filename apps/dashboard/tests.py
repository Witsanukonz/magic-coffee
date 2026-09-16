import tempfile
import uuid
from datetime import timedelta
from decimal import Decimal
from io import BytesIO, StringIO
from pathlib import Path
from PIL import Image
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from apps.accounts.models import User
from apps.cart.models import Cart, CartItem
from apps.menu.models import Category, MenuItem
from apps.orders.models import LoyaltyAccount, Order
from apps.orders.services import place_order, change_status


class CoffeeWorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user('admin_test', email='admin@example.com', password='TestingCoffee!2026', role='admin')
        cls.customer = User.objects.create_user('customer_test', email='customer@example.com', password='TestingCoffee!2026')
        cls.other = User.objects.create_user('other_test', email='other@example.com', password='TestingCoffee!2026')
        cls.category = Category.objects.create(name='Coffee')
        cls.item = MenuItem.objects.create(name='Cafe Latte', category=cls.category, price=85, stock=20,
            description='Silky espresso and milk', available_sizes=['Small','Medium','Large'], is_featured=True)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.settings_override = override_settings(MEDIA_ROOT=Path(self.temp.name))
        self.settings_override.enable()
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(self.settings_override.disable)

    def url(self, name, resource='menu', pk=None):
        kwargs = {'resource': resource}
        if pk: kwargs['pk'] = pk
        return reverse(name, kwargs=kwargs)

    def add(self, quantity=1, **options):
        return self.client.post(reverse('cart_add', args=[self.item.pk]),
            {'quantity':quantity,'size':'Large','temperature':'Iced','sweetness':'50', **options})

    def order_data(self):
        return {'full_name':'Test Customer','phone':'0812345678','order_type':'take_away','note':'No straw', 'checkout_token':uuid.uuid4()}

    def create_order(self, user=None, quantity=2):
        user = user or self.customer
        cart = Cart.objects.create(user=user)
        CartItem.objects.create(cart=cart, menu_item=self.item, quantity=quantity, size='Large', temperature='Iced', sweetness='50')
        return place_order(user, cart, self.order_data())

    def menu_data(self, **changes):
        return {'name':'New Latte','category':self.category.pk,'description':'Freshly made latte', 'price':'95.00','stock':'10',
            'menu_type':'coffee','temperature_option':'both','available_sizes':['Small','Large'],'is_available':'on',
            'available_date':timezone.localdate().isoformat(), **changes}

    def user_data(self, **changes):
        return {'username':'new_customer','email':'new@example.com','first_name':'New','last_name':'Customer',
            'role':'customer','is_active':'on','password1':'AnotherCoffee!2026','password2':'AnotherCoffee!2026', **changes}

    def test_public_pages_and_detail_render(self):
        for path in ['/', '/about/', '/menu/', '/menu/cafe-latte/', '/cart/', '/accounts/login/',
                     '/accounts/register/', '/accounts/password-reset/']:
            with self.subTest(path=path): self.assertEqual(self.client.get(path).status_code,200)

    def test_search_matches_name_description_category(self):
        for q in ['Latte','Silky','Coffee']:
            self.assertContains(self.client.get('/menu/', {'q':q}), 'Cafe Latte')
        self.assertContains(self.client.get('/menu/', {'q':'unmatched'}), 'No drinks found')

    def test_filters_sort_and_pagination_preserve_query(self):
        for i in range(26):
            MenuItem.objects.create(category=self.category,name=f'Coffee {i}',price=30+i,stock=5,description='Coffee')
        response=self.client.get('/menu/', {'category':'coffee','sort':'price_low','page':2})
        self.assertEqual(len(response.context['page_obj']),12)
        self.assertEqual(response.context['page_obj'].number,2)
        self.assertContains(response,'category=coffee')
        prices=[x.price for x in response.context['page_obj']]
        self.assertEqual(prices,sorted(prices))
        filtered=self.client.get('/menu/', {'min_price':80,'max_price':90})
        self.assertEqual(filtered.context['page_obj'].paginator.count,1)
        self.assertContains(self.client.get('/menu/',{'min_price':'NaN'}),'valid non-negative price')

    def test_availability_and_inactive_categories(self):
        self.item.available_date=timezone.localdate()+timedelta(days=1)
        self.item.save()
        self.assertEqual(self.client.get('/menu/',{'availability':'available'}).context['page_obj'].paginator.count,0)
        self.assertEqual(self.add().status_code,400)
        self.category.is_active=False
        self.category.save()
        self.assertEqual(self.client.get('/menu/cafe-latte/').status_code,404)

    def test_register_hashes_password_and_cannot_escalate_role(self):
        response=self.client.post('/accounts/register/',self.user_data(role='admin'))
        self.assertEqual(response.status_code,302)
        user=User.objects.get(username='new_customer')
        self.assertEqual(user.role,'customer')
        self.assertTrue(user.check_password('AnotherCoffee!2026'))
        self.assertNotEqual(user.password,'AnotherCoffee!2026')

    def test_register_rejects_invalid_email_weak_password_and_duplicates(self):
        for values in [dict(email='bad'),dict(password1='123',password2='123'),dict(email=self.customer.email)]:
            response=self.client.post('/accounts/register/',self.user_data(**values))
            self.assertEqual(response.status_code,200)
            self.assertTrue(response.context['form'].errors)
        self.assertFalse(User.objects.filter(username='new_customer').exists())

    def test_login_logout_and_safe_redirect(self):
        response=self.client.post('/accounts/login/',{'username':'admin_test','password':'TestingCoffee!2026','next':'https://evil.example/'})
        self.assertRedirects(response,'/dashboard/')
        self.assertEqual(self.client.get('/accounts/logout/').status_code,405)
        self.assertEqual(self.client.post('/accounts/logout/').status_code,302)
        self.customer.is_active=False;self.customer.save()
        response=self.client.post('/accounts/login/',{'username':'customer_test','password':'TestingCoffee!2026'})
        self.assertTrue(response.context['form'].errors)

    def test_guest_cart_merges_on_login(self):
        self.add()
        response=self.client.post('/accounts/login/',{'username':'customer_test','password':'TestingCoffee!2026'})
        self.assertEqual(response.status_code,302)
        self.assertEqual(Cart.objects.get(user=self.customer).items.get().size,'Large')
        self.assertFalse(Cart.objects.filter(user__isnull=True).exists())

    def test_cart_options_add_update_remove_and_foreign_access(self):
        self.client.force_login(self.customer)
        self.assertEqual(self.add(quantity=2).status_code,302)
        line=CartItem.objects.get()
        self.assertEqual(line.subtotal,170)
        response = self.client.post(reverse('cart_update',args=[line.pk]),{'quantity':3}, HTTP_ACCEPT='application/json')
        self.assertEqual(Decimal(response.json()['cart_total']), Decimal('255.00'))
        line.refresh_from_db();self.assertEqual(line.quantity,3)
        foreign=Client();foreign.force_login(self.other)
        self.assertEqual(foreign.post(reverse('cart_remove',args=[line.pk])).status_code,404)
        self.client.post(reverse('cart_remove',args=[line.pk]))
        self.assertFalse(CartItem.objects.exists())

    def test_cart_rejects_invalid_options_negative_and_total_stock(self):
        for data in [dict(quantity=0),dict(quantity=-1),dict(quantity=21),dict(size='XL'),dict(temperature='Frozen'),dict(sweetness='101')]:
            self.assertEqual(self.add(**data).status_code,400)
        self.add(quantity=15)
        self.assertEqual(self.add(quantity=6,size='Small').status_code,400)
        line=CartItem.objects.get()
        self.client.post(reverse('cart_update',args=[line.pk]),{'quantity':0})
        line.refresh_from_db();self.assertEqual(line.quantity,15)

    def test_food_has_no_drink_options_and_quick_add_works(self):
        self.item.menu_type='bakery';self.item.available_sizes=[];self.item.save()
        response=self.client.get('/menu/cafe-latte/')
        self.assertNotContains(response,'name="sweetness"')
        self.client.post(reverse('cart_add',args=[self.item.pk]),{'quick':1})
        self.assertEqual(CartItem.objects.get().size,'')

    def test_checkout_requires_login(self):
        self.assertRedirects(self.client.get('/checkout/'),'/accounts/login/?next=/checkout/')

    def test_full_checkout_snapshot_stock_and_duplicate_submit(self):
        self.client.force_login(self.customer)
        self.add(quantity=2)
        response=self.client.get('/checkout/')
        token=response.context['form'].initial['checkout_token']
        data=self.order_data();data['checkout_token']=token
        response=self.client.post('/checkout/',data)
        order=Order.objects.get()
        self.assertRedirects(response,reverse('order_success',args=[order.pk]))
        self.assertEqual(order.status,'pending');self.assertEqual(order.total_price,170)
        self.assertTrue(order.order_number.startswith('MC'))
        line=order.items.get();self.assertEqual((line.size,line.temperature,line.sweetness),('Large','Iced','50'))
        self.item.refresh_from_db();self.assertEqual(self.item.stock,18)
        self.assertFalse(CartItem.objects.exists())
        self.client.post('/checkout/',data)
        self.assertEqual(Order.objects.count(),1)
        self.item.name='Renamed';self.item.price=999;self.item.save()
        line.refresh_from_db();self.assertEqual(line.menu_name,'Cafe Latte');self.assertEqual(line.price,85)

    def test_checkout_validation_and_expired_token(self):
        self.client.force_login(self.customer);self.add()
        self.client.get('/checkout/')
        response=self.client.post('/checkout/',self.order_data())
        self.assertContains(response,'checkout expired')
        data=self.order_data();data['checkout_token']=self.client.session['checkout_token'];data['phone']='bad'
        self.assertTrue(self.client.post('/checkout/',data).context['form'].errors)
        data['phone']='--------'
        self.assertTrue(self.client.post('/checkout/',data).context['form'].errors)
        self.assertFalse(Order.objects.exists())

    def test_out_of_stock_checkout_rolls_back_all_lines(self):
        cart=Cart.objects.create(user=self.customer)
        other_item=MenuItem.objects.create(name='Tea',category=self.category,price=70,stock=1,description='Tea',menu_type='bakery')
        CartItem.objects.create(cart=cart,menu_item=self.item,quantity=2,size='Large',temperature='Iced',sweetness='50')
        CartItem.objects.create(cart=cart,menu_item=other_item,quantity=2)
        with self.assertRaises(ValueError):place_order(self.customer,cart,self.order_data())
        self.item.refresh_from_db();self.assertEqual(self.item.stock,20)
        self.assertEqual(cart.items.count(),2);self.assertFalse(Order.objects.exists())

    def test_changed_drink_options_block_stale_cart(self):
        cart=Cart.objects.create(user=self.customer)
        CartItem.objects.create(cart=cart,menu_item=self.item,quantity=1,size='XL',temperature='Iced',sweetness='50')
        with self.assertRaises(ValueError):place_order(self.customer,cart,self.order_data())
        self.assertFalse(Order.objects.exists())

    def test_order_owner_permissions_and_profile_isolation(self):
        order=self.create_order()
        self.client.force_login(self.other)
        for name in ['order_detail','order_status','order_success']:
            self.assertEqual(self.client.get(reverse(name,args=[order.pk])).status_code,404)
        self.client.post('/accounts/profile/',{'email':'updated@example.com','first_name':'Other','last_name':'Person','role':'admin','id':self.customer.pk})
        self.other.refresh_from_db();self.customer.refresh_from_db()
        self.assertEqual(self.other.role,'customer');self.assertEqual(self.customer.email,'customer@example.com')
        self.client.force_login(self.customer)
        for path in ['/orders/',reverse('order_detail',args=[order.pk]),reverse('order_success',args=[order.pk]),'/accounts/profile/']:
            self.assertEqual(self.client.get(path).status_code,200)
        response = self.client.get(reverse('order_status', args=[order.pk]))
        self.assertEqual(response.json()['status'], 'pending')
        self.assertEqual(response['Cache-Control'], 'no-store')

    def test_dashboard_permission_every_resource_endpoint(self):
        self.client.force_login(self.customer)
        for resource,pk in [('menu',self.item.pk),('categories',self.category.pk),('users',self.other.pk)]:
            for name in ['dashboard_resource','dashboard_add','dashboard_detail','dashboard_edit','dashboard_delete']:
                path=self.url(name,resource,pk if name in ['dashboard_detail','dashboard_edit','dashboard_delete'] else None)
                for method in ['get','post']:
                    self.assertEqual(getattr(self.client,method)(path).status_code,403)
        for path in ['/dashboard/','/dashboard/orders/', '/dashboard/orders/1/',f'/dashboard/users/{self.other.pk}/toggle/']:
            self.assertEqual(self.client.get(path).status_code,403)

    def test_admin_all_dashboard_pages_render(self):
        order=self.create_order();self.client.force_login(self.admin)
        paths=['/dashboard/','/dashboard/orders/',f'/dashboard/orders/{order.pk}/']
        for resource,pk in [('menu',self.item.pk),('categories',self.category.pk),('users',self.customer.pk)]:
            paths.extend([self.url('dashboard_resource',resource),self.url('dashboard_add',resource),
                          self.url('dashboard_detail',resource,pk),self.url('dashboard_edit',resource,pk)])
        for path in paths:
            with self.subTest(path=path):self.assertEqual(self.client.get(path).status_code,200)

    def test_admin_menu_crud_and_delete_preserves_order(self):
        order=self.create_order();self.client.force_login(self.admin)
        self.assertEqual(self.client.post(self.url('dashboard_add'),self.menu_data()).status_code,302)
        item=MenuItem.objects.get(name='New Latte')
        self.client.post(self.url('dashboard_edit',pk=item.pk),self.menu_data(price='110',stock=3))
        item.refresh_from_db();self.assertEqual(item.price,110);self.assertEqual(item.stock,3)
        self.assertEqual(self.client.get(self.url('dashboard_delete',pk=item.pk)).status_code,405)
        self.assertContains(self.client.get(self.url('dashboard_resource')),'data-delete-url')
        self.client.post(self.url('dashboard_delete',pk=item.pk));self.assertFalse(MenuItem.objects.filter(pk=item.pk).exists())
        self.client.post(self.url('dashboard_delete',pk=self.item.pk))
        line=order.items.get();self.assertIsNone(line.menu_item);self.assertEqual(line.menu_name,'Cafe Latte')

    def test_menu_validation_required_fields_negative_and_sizes(self):
        self.client.force_login(self.admin)
        for changes in [dict(price=-1),dict(stock=-1),dict(name=''),dict(category=''),dict(available_sizes=[])]:
            response=self.client.post(self.url('dashboard_add'),self.menu_data(**changes))
            self.assertEqual(response.status_code,200);self.assertTrue(response.context['form'].errors)
        self.assertEqual(MenuItem.objects.count(),1)

    def test_image_upload_and_malicious_file_rejection(self):
        self.client.force_login(self.admin)
        image=BytesIO();Image.new('RGB',(50,50),'brown').save(image,format='PNG')
        data=self.menu_data(image=SimpleUploadedFile('coffee.png',image.getvalue(),content_type='image/png'))
        self.assertEqual(self.client.post(self.url('dashboard_add'),data).status_code,302)
        self.assertTrue(Path(MenuItem.objects.get(name='New Latte').image.path).exists())
        for filename in ['fake.jpg','payload.svg']:
            response=self.client.post(self.url('dashboard_add'),self.menu_data(name='Bad image',image=SimpleUploadedFile(filename,b'<script>alert(1)</script>')))
            self.assertTrue(response.context['form'].errors)
        self.assertFalse(MenuItem.objects.filter(name='Bad image').exists())

    def test_user_crud_password_reset_toggle_and_self_protection(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.post(self.url('dashboard_add','users'),self.user_data()).status_code,302)
        user=User.objects.get(username='new_customer');self.assertTrue(user.check_password('AnotherCoffee!2026'))
        original=user.password
        self.client.post(self.url('dashboard_edit','users',user.pk),self.user_data(first_name='Changed',password1='',password2=''))
        user.refresh_from_db();self.assertEqual(user.first_name,'Changed');self.assertEqual(user.password,original)
        self.client.post(self.url('dashboard_edit','users',user.pk),self.user_data(password1='FreshCoffee!2026',password2='FreshCoffee!2026'))
        user.refresh_from_db();self.assertTrue(user.check_password('FreshCoffee!2026'))
        self.client.post(reverse('dashboard_user_toggle',args=[user.pk]));user.refresh_from_db();self.assertFalse(user.is_active)
        self.client.post(reverse('dashboard_user_toggle',args=[user.pk]));user.refresh_from_db();self.assertTrue(user.is_active)
        self.client.post(self.url('dashboard_delete','users',self.admin.pk));self.assertTrue(User.objects.filter(pk=self.admin.pk).exists())
        self.client.post(reverse('dashboard_user_toggle',args=[self.admin.pk]));self.admin.refresh_from_db();self.assertTrue(self.admin.is_active)
        data=self.user_data(username='admin_test',email=self.admin.email,role='customer',password1='',password2='')
        self.assertTrue(self.client.post(self.url('dashboard_edit','users',self.admin.pk),data).context['form'].errors)
        self.client.post(self.url('dashboard_delete','users',user.pk));self.assertFalse(User.objects.filter(pk=user.pk).exists())

    def test_category_crud_and_protected_delete(self):
        self.client.force_login(self.admin)
        self.client.post(self.url('dashboard_add','categories'),{'name':'Bakery','description':'Fresh bites','is_active':'on'})
        category=Category.objects.get(name='Bakery')
        self.client.post(self.url('dashboard_edit','categories',category.pk),{'name':'Fresh Bakery','description':'Baked daily','is_active':'on'})
        category.refresh_from_db();self.assertEqual(category.name,'Fresh Bakery')
        self.client.post(self.url('dashboard_delete','categories',category.pk));self.assertFalse(Category.objects.filter(pk=category.pk).exists())
        self.client.post(self.url('dashboard_delete','categories',self.category.pk));self.assertTrue(Category.objects.filter(pk=self.category.pk).exists())

    def test_order_status_flow_and_customer_visibility(self):
        order=self.create_order();self.client.force_login(self.admin)
        for status in ['preparing','ready','completed']:
            self.client.post(reverse('dashboard_order',args=[order.pk]),{'status':status})
            order.refresh_from_db();self.assertEqual(order.status,status)
        with self.assertRaises(ValueError):change_status(order.pk,'pending')
        self.client.force_login(self.customer)
        self.assertContains(self.client.get(reverse('order_detail',args=[order.pk])),'Completed')
        live_status = self.client.get(reverse('order_status', args=[order.pk])).json()
        self.assertEqual(live_status['loyalty'], {'completed_purchases': 1, 'reward_balance': 0})

    def test_cancel_restores_stock_exactly_once(self):
        order=self.create_order(quantity=3)
        self.item.refresh_from_db();self.assertEqual(self.item.stock,17)
        change_status(order.pk,'cancelled');change_status(order.pk,'cancelled')
        self.item.refresh_from_db();self.assertEqual(self.item.stock,20)
        with self.assertRaises(ValueError):change_status(order.pk,'preparing')

    def test_loyalty_awards_a_free_coffee_after_ten_completed_purchases(self):
        for _ in range(10):
            cart, _ = Cart.objects.get_or_create(user=self.customer)
            CartItem.objects.create(cart=cart, menu_item=self.item, quantity=1, size='Large', temperature='Iced', sweetness='50')
            order = place_order(self.customer, cart, self.order_data())
            for status in ['preparing', 'ready', 'completed']:
                change_status(order.pk, status)
        account = LoyaltyAccount.objects.get(phone='0812345678')
        self.assertEqual(account.completed_purchases, 10)
        self.assertEqual(account.reward_balance, 1)

    def test_loyalty_reward_uses_phone_and_is_restored_when_order_is_cancelled(self):
        account = LoyaltyAccount.objects.create(phone='0812345678', reward_balance=1)
        cart = Cart.objects.create(user=self.customer)
        line = CartItem.objects.create(cart=cart, menu_item=self.item, quantity=1, size='Large', temperature='Iced', sweetness='50')
        data = self.order_data()
        data['phone'] = '081-234-5678'
        order = place_order(self.customer, cart, data, reward_line_id=line.pk)
        account.refresh_from_db()
        self.assertEqual(order.total_price, Decimal('0.00'))
        self.assertEqual(order.loyalty_discount, Decimal('85.00'))
        self.assertTrue(order.loyalty_reward_redeemed)
        self.assertEqual(account.reward_balance, 0)
        change_status(order.pk, 'cancelled')
        account.refresh_from_db()
        self.assertEqual(account.reward_balance, 1)

    def test_loyalty_reward_status_only_unlocks_after_ten_completed_purchases(self):
        self.client.force_login(self.customer)
        account = LoyaltyAccount.objects.create(phone='0812345678', completed_purchases=9)
        locked = self.client.post(reverse('loyalty_status'), {'phone': '0812345678'}).json()
        self.assertFalse(locked['eligible'])
        self.assertEqual(locked['visits_remaining'], 1)
        account.completed_purchases = 10
        account.reward_balance = 1
        account.save(update_fields=['completed_purchases', 'reward_balance'])
        unlocked = self.client.post(reverse('loyalty_status'), {'phone': '081-234-5678'}).json()
        self.assertTrue(unlocked['eligible'])
        self.assertEqual(unlocked['reward_balance'], 1)

    def test_dashboard_search_filters_pagination(self):
        self.client.force_login(self.admin)
        for i in range(11):User.objects.create_user(f'person{i}',email=f'person{i}@example.com')
        response=self.client.get('/dashboard/users/',{'role':'customer'})
        self.assertEqual(len(response.context['page_obj']),10)
        self.assertEqual(self.client.get('/dashboard/users/',{'q':'person10'}).context['page_obj'].paginator.count,1)
        self.assertEqual(self.client.get('/dashboard/menu/',{'q':'Latte','category':'coffee','status':'active'}).context['page_obj'].paginator.count,1)
        self.item.stock=0;self.item.save()
        self.assertEqual(self.client.get('/dashboard/menu/',{'status':'active'}).context['page_obj'].paginator.count,0)
        self.assertEqual(self.client.get('/dashboard/menu/',{'status':'inactive'}).context['page_obj'].paginator.count,1)
        self.item.stock=20;self.item.save()
        order=self.create_order()
        self.assertEqual(self.client.get('/dashboard/orders/',{'q':order.order_number,'status':'pending'}).context['page_obj'].paginator.count,1)

    def test_dashboard_board_and_menu_availability_toggle(self):
        order = self.create_order()
        self.client.force_login(self.admin)
        response = self.client.get('/dashboard/orders/')
        self.assertContains(response, 'LIVE ORDERS')
        self.assertEqual(len(response.context['board']), 4)
        self.assertContains(response, order.order_number)
        response = self.client.post(reverse('dashboard_order', args=[order.pk]), {'status': 'preparing', 'from_board': '1'})
        self.assertRedirects(response, reverse('dashboard_orders'))
        order.refresh_from_db()
        self.assertEqual(order.status, 'preparing')
        self.client.post(reverse('dashboard_menu_availability', args=[self.item.pk]))
        self.item.refresh_from_db()
        self.assertFalse(self.item.is_available)

    def test_live_admin_order_fragments_require_admin_and_include_new_order(self):
        order = self.create_order()
        for path in [reverse('dashboard_live_recent_orders'), reverse('dashboard_live_order_board')]:
            self.client.force_login(self.customer)
            self.assertEqual(self.client.get(path).status_code, 403)
            self.client.force_login(self.admin)
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, order.order_number)
            self.assertEqual(response['Cache-Control'], 'no-store')

    def test_live_sidebar_alerts_put_new_order_count_on_live_orders_and_stock_warnings_in_panel(self):
        order = self.create_order()
        self.item.stock = 0
        self.item.save(update_fields=['stock'])
        self.client.force_login(self.customer)
        self.assertEqual(self.client.get(reverse('dashboard_live_sidebar_alerts')).status_code, 403)
        self.client.force_login(self.admin)
        response = self.client.get(reverse('dashboard_live_sidebar_alerts'))
        payload = response.json()
        alerts = payload['alerts']
        self.assertEqual(payload['pending_order_count'], 1)
        self.assertTrue(any(alert['id'] == f'out-{self.item.pk}' for alert in alerts))
        self.assertEqual(response['Cache-Control'], 'no-store')

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_password_reset_end_to_end(self):
        self.client.post('/accounts/password-reset/',{'email':self.customer.email})
        self.assertEqual(len(mail.outbox),1)
        link=next(line for line in mail.outbox[0].body.splitlines() if line.startswith('http'))
        response=self.client.get(link,follow=True)
        self.assertTrue(response.context['validlink'])
        response=self.client.post(response.request['PATH_INFO'],{'new_password1':'ResetCoffee!2026','new_password2':'ResetCoffee!2026'})
        self.assertRedirects(response,'/accounts/reset/complete/')
        self.customer.refresh_from_db();self.assertTrue(self.customer.check_password('ResetCoffee!2026'))

    def test_csrf_required_for_mutations(self):
        strict=Client(enforce_csrf_checks=True)
        strict.force_login(self.admin)
        for path in [reverse('cart_add',args=[self.item.pk]),self.url('dashboard_delete',pk=self.item.pk),'/checkout/','/accounts/logout/']:
            self.assertEqual(strict.post(path).status_code,403)


class SeedTests(TestCase):
    def test_seed_idempotent_preserves_edits_and_all_images_exist(self):
        with tempfile.TemporaryDirectory() as folder, override_settings(MEDIA_ROOT=Path(folder)):
            call_command('seed_demo',stdout=StringIO())
            self.assertEqual(MenuItem.objects.count(),28);self.assertEqual(Category.objects.count(),6)
            item=MenuItem.objects.get(slug='cafe-latte');item.stock=7;item.price=101;item.save()
            category=Category.objects.get(slug='coffee');category.name='Specialty Coffee';category.save()
            password=User.objects.get(username='demo_customer').password
            call_command('seed_demo',stdout=StringIO())
            self.assertEqual(MenuItem.objects.count(),28);self.assertEqual(User.objects.count(),2)
            item.refresh_from_db();self.assertEqual(item.stock,7);self.assertEqual(item.price,101)
            category.refresh_from_db();self.assertEqual(category.name,'Specialty Coffee')
            self.assertEqual(User.objects.get(username='demo_customer').password,password)
            for obj in list(MenuItem.objects.all())+list(Category.objects.all()):
                self.assertTrue(Path(obj.image.path).is_file())
                Image.open(obj.image.path).verify()
