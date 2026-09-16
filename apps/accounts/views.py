from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from apps.cart.services import merge_guest_cart
from .forms import RegisterForm, ProfileForm


class StoreLoginView(LoginView):
    template_name = 'accounts/form.html'
    extra_context = {'title': 'Welcome back.', 'subtitle': 'Your everyday favorites are waiting.', 'button': 'SIGN IN', 'mode': 'login'}

    def form_valid(self, form):
        guest_key = self.request.session.session_key
        response = super().form_valid(form)
        merge_guest_cart(self.request.user, guest_key)
        return response

    def get_success_url(self):
        return self.get_redirect_url() or ('/dashboard/' if self.request.user.is_admin else '/')


def register(request):
    if request.user.is_authenticated:
        return redirect('home')
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        guest_key = request.session.session_key
        user = form.save()
        login(request, user)
        merge_guest_cart(user, guest_key)
        messages.success(request, 'Your account is ready. Welcome to MAGIC COFFEE.')
        return redirect('menu_list')
    return render(request, 'accounts/form.html', {'form': form, 'title': 'Make yourself at home.',
        'subtitle': 'Create an account for coffee, fresh bites, and everyday moments.', 'button': 'CREATE ACCOUNT', 'mode': 'register'})


@login_required
def profile(request):
    form = ProfileForm(request.POST or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('profile')
    return render(request, 'accounts/form.html', {'form': form, 'title': 'Your profile.',
        'subtitle': 'A few details that make it yours.', 'button': 'SAVE CHANGES'})
