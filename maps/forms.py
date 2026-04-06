from django import forms
from .models import Location, DistributionRequest

class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ['title', 'description', 'latitude', 'longitude']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'latitude': forms.NumberInput(attrs={'step': '0.000001'}),
            'longitude': forms.NumberInput(attrs={'step': '0.000001'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})


# НОВАЯ ФОРМА: Заявка на дистрибутив
class DistributionRequestForm(forms.ModelForm):
    """Форма для добавления заявки на дистрибутив"""

    class Meta:
        model = DistributionRequest
        fields = [
            'company_name', 'business_type', 'description',
            'contact_person', 'phone', 'email',
            'latitude', 'longitude', 'address', 'city',
            'employees_count', 'need_1c_buh', 'need_1c_trade',
            'need_1c_salary', 'need_cloud', 'comment'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'comment': forms.Textarea(attrs={'rows': 3}),
            'latitude': forms.NumberInput(attrs={'step': '0.000001', 'readonly': 'readonly'}),
            'longitude': forms.NumberInput(attrs={'step': '0.000001', 'readonly': 'readonly'}),
            'address': forms.TextInput(attrs={'readonly': 'readonly'}),
            'city': forms.TextInput(attrs={'readonly': 'readonly'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if hasattr(field.widget, 'attrs'):
                field.widget.attrs.update({'class': 'form-control'})

        self.fields['business_type'].widget.attrs.update({'class': 'form-select'})

        for field in ['need_1c_buh', 'need_1c_trade', 'need_1c_salary', 'need_cloud']:
            self.fields[field].widget.attrs.update({'class': 'form-check-input'})