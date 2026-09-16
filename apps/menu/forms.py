from django import forms
from .models import Category, MenuItem


class MenuForm(forms.ModelForm):
    available_sizes = forms.MultipleChoiceField(choices=[(x, x) for x in ['Small', 'Medium', 'Large']],
                                               widget=forms.CheckboxSelectMultiple, required=False)
    temperature_option = forms.ChoiceField(choices=MenuItem._meta.get_field('temperature_option').choices,
                                           widget=forms.RadioSelect)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].required = False

    class Meta:
        model = MenuItem
        fields = ['name', 'category', 'description', 'price', 'stock', 'menu_type', 'temperature_option',
                  'available_sizes', 'is_available', 'is_featured', 'image', 'available_date']
        widgets = {'description': forms.Textarea(attrs={'rows': 4}),
                   'available_date': forms.DateInput(attrs={'type': 'date'}),
                   'image': forms.FileInput(attrs={'accept': '.jpg,.jpeg,.png,.webp', 'data-preview': 'image-preview'}),
                   'price': forms.NumberInput(attrs={'min': 0, 'step': '0.01'}),
                   'stock': forms.NumberInput(attrs={'min': 0})}

    def clean(self):
        data = super().clean()
        if data.get('menu_type') in ('coffee', 'non-coffee', 'tea') and not data.get('available_sizes'):
            self.add_error('available_sizes', 'Choose at least one size for drinks.')
        return data


class CategoryForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].required = False

    class Meta:
        model = Category
        fields = ['name', 'description', 'image', 'is_active']
        widgets = {'description': forms.Textarea(attrs={'rows': 4}),
                   'image': forms.FileInput(attrs={'accept': '.jpg,.jpeg,.png,.webp', 'data-preview': 'image-preview'})}
