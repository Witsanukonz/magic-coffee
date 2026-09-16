from django import forms
from django.core.validators import RegexValidator
from .models import Order


class CheckoutForm(forms.ModelForm):
    order_type = forms.ChoiceField(choices=Order._meta.get_field('order_type').choices, widget=forms.RadioSelect)
    phone = forms.CharField(max_length=25, validators=[RegexValidator(r'^\+?[0-9 ()-]{8,25}$', 'Enter a valid phone number.')])
    checkout_token = forms.UUIDField(widget=forms.HiddenInput)

    def __init__(self, *args, cart=None, loyalty_account=None, **kwargs):
        super().__init__(*args, **kwargs)
        eligible_lines = [line for line in (cart.items.select_related('menu_item') if cart else [])
                          if line.menu_item.menu_type == 'coffee']
        if eligible_lines:
            self.fields['reward_line'] = forms.ChoiceField(
                label='FREE COFFEE REWARD', required=False,
                choices=[('', 'Keep my free coffee for later')] + [
                    (str(line.pk), f'Use 1 reward for {line.menu_item.name}') for line in eligible_lines],
                help_text='One reward makes one coffee free. Enter the phone number linked to your rewards.')

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        digits = ''.join(char for char in phone if char.isdigit())
        if not 8 <= len(digits) <= 15:
            raise forms.ValidationError('Phone number must contain 8 to 15 digits.')
        return phone

    class Meta:
        model = Order
        fields = ['full_name', 'phone', 'order_type', 'note']
        widgets = {'order_type': forms.RadioSelect, 'note': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Anything we should know?'})}
