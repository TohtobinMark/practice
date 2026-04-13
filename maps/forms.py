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


from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User

class CustomUserCreationForm(UserCreationForm):
    """Кастомная форма регистрации с использованием модели User"""

    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+7 (XXX) XXX-XX-XX'})
    )
    company_name = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название компании'})
    )

    class Meta:
        model = User  # Указываем вашу кастомную модель
        fields = ('username', 'password1', 'password2', 'phone', 'company_name')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Настройка классов для полей
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
        self.fields['phone'].widget.attrs.update({'class': 'form-control'})
        self.fields['company_name'].widget.attrs.update({'class': 'form-control'})

        # Настройка меток
        self.fields['phone'].label = 'Телефон'
        self.fields['company_name'].label = 'Название компании'


class CustomAuthenticationForm(AuthenticationForm):
    """Кастомная форма аутентификации"""

    class Meta:
        model = User
        fields = ('username', 'password')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['password'].widget.attrs.update({'class': 'form-control'})