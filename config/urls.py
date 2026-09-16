from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth
from django.urls import path
from apps.accounts import views as accounts
from apps.menu import views as menu
from apps.cart import views as cart
from apps.orders import views as orders
from apps.dashboard import views as dashboard

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', menu.home, name='home'), path('about/', menu.about, name='about'),
    path('menu/', menu.menu_list, name='menu_list'), path('menu/<slug:slug>/', menu.menu_detail, name='menu_detail'),
    path('accounts/register/', accounts.register, name='register'),
    path('accounts/login/', accounts.StoreLoginView.as_view(), name='login'),
    path('accounts/logout/', auth.LogoutView.as_view(), name='logout'),
    path('accounts/profile/', accounts.profile, name='profile'),
    path('accounts/password-reset/', auth.PasswordResetView.as_view(template_name='accounts/form.html',
         email_template_name='accounts/reset_email.txt', subject_template_name='accounts/reset_subject.txt',
         extra_context={'title': 'A fresh start.', 'subtitle': 'Enter your account email. In this classroom demo, the reset link appears in the server terminal.', 'button': 'RESET PASSWORD'}), name='password_reset'),
    path('accounts/password-reset/done/', auth.PasswordResetDoneView.as_view(template_name='accounts/reset_done.html'), name='password_reset_done'),
    path('accounts/reset/<uidb64>/<token>/', auth.PasswordResetConfirmView.as_view(template_name='accounts/reset_confirm.html'), name='password_reset_confirm'),
    path('accounts/reset/complete/', auth.PasswordResetCompleteView.as_view(template_name='accounts/reset_complete.html'), name='password_reset_complete'),
    path('cart/', cart.cart_detail, name='cart'), path('cart/add/<int:pk>/', cart.cart_add, name='cart_add'),
    path('cart/update/<int:pk>/', cart.cart_update, name='cart_update'),
    path('cart/remove/<int:pk>/', cart.cart_remove, name='cart_remove'),
    path('checkout/', orders.checkout, name='checkout'), path('loyalty/status/', orders.loyalty_status, name='loyalty_status'), path('orders/', orders.order_list, name='orders'),
    path('orders/<int:pk>/', orders.order_detail, name='order_detail'),
    path('orders/<int:pk>/status/', orders.order_status, name='order_status'),
    path('orders/<int:pk>/success/', orders.order_success, name='order_success'),
    path('dashboard/', dashboard.overview, name='dashboard'),
    path('dashboard/live-orders/', dashboard.live_recent_orders, name='dashboard_live_recent_orders'),
    path('dashboard/alerts/live/', dashboard.live_sidebar_alerts, name='dashboard_live_sidebar_alerts'),
    path('dashboard/orders/', dashboard.order_list, name='dashboard_orders'),
    path('dashboard/orders/live/', dashboard.live_order_board, name='dashboard_live_order_board'),
    path('dashboard/orders/<int:pk>/', dashboard.order_detail, name='dashboard_order'),
    path('dashboard/menu/<int:pk>/availability/', dashboard.menu_availability, name='dashboard_menu_availability'),
    path('dashboard/users/<int:pk>/toggle/', dashboard.user_toggle, name='dashboard_user_toggle'),
]
for resource in ['menu', 'categories', 'users']:
    urlpatterns += [
        path(f'dashboard/{resource}/', dashboard.resource_list, {'resource': resource}, name='dashboard_resource'),
        path(f'dashboard/{resource}/add/', dashboard.resource_edit, {'resource': resource}, name='dashboard_add'),
        path(f'dashboard/{resource}/<int:pk>/', dashboard.resource_detail, {'resource': resource}, name='dashboard_detail'),
        path(f'dashboard/{resource}/<int:pk>/edit/', dashboard.resource_edit, {'resource': resource}, name='dashboard_edit'),
        path(f'dashboard/{resource}/<int:pk>/delete/', dashboard.resource_delete, {'resource': resource}, name='dashboard_delete'),
    ]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
