from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.password_validation import validate_password
from .models import User


class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']


class AdminUserForm(forms.ModelForm):
    password1 = forms.CharField(label='New password', widget=forms.PasswordInput, required=False,
                                help_text='Leave blank when editing to keep the current password.')
    password2 = forms.CharField(label='Confirm password', widget=forms.PasswordInput, required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'is_active']

    def __init__(self, *args, **kwargs):
        self.actor = kwargs.pop('actor', None)
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['password1'].required = True
            self.fields['password2'].required = True

    def clean(self):
        data = super().clean()
        password = data.get('password1')
        if password != data.get('password2'):
            self.add_error('password2', 'Passwords do not match.')
        if self.instance.pk == getattr(self.actor, 'pk', None):
            if not data.get('is_active') or data.get('role') != 'admin':
                raise forms.ValidationError('You cannot disable or demote your own account.')
        if password:
            candidate = User(username=data.get('username', ''), email=data.get('email', ''),
                             first_name=data.get('first_name', ''), last_name=data.get('last_name', ''))
            validate_password(password, candidate)
        return data

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data.get('password1'):
            user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user
