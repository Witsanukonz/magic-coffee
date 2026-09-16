from django import forms


class AddCartForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, max_value=999, initial=1)
    size = forms.ChoiceField(required=False)
    temperature = forms.ChoiceField(required=False)
    sweetness = forms.ChoiceField(choices=[(str(n), f'{n}%') for n in [0, 25, 50, 75, 100]], required=False)

    def __init__(self, *args, item, **kwargs):
        super().__init__(*args, **kwargs)
        if item.is_drink:
            self.fields['size'].choices = [(x, x) for x in item.available_sizes]
            self.fields['temperature'].choices = [(x, x) for x in item.temperatures]
            for name in ['size', 'temperature', 'sweetness']:
                self.fields[name].required = True
            self.initial.update(size=next(iter(item.available_sizes), ''), temperature=item.temperatures[0], sweetness='50')
        else:
            for name in ['size', 'temperature', 'sweetness']:
                del self.fields[name]
