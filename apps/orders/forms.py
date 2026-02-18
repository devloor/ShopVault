import re
from django import forms
from django.core.validators import RegexValidator


name_validator = RegexValidator(
    regex=r'^[a-zA-Z\s\-\.]+$',
    message='Name may only contain letters, spaces, hyphens, and periods.'
)


class CheckoutForm(forms.Form):
    """Checkout form with input validation."""

    full_name = forms.CharField(
        max_length=100,
        min_length=2,
        validators=[name_validator],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Full name',
        }),
        error_messages={
            'required': 'Please enter your full name.',
            'min_length': 'Name must be at least 2 characters.',
        }
    )

    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email address',
        }),
        error_messages={
            'required': 'Please enter your email address.',
            'invalid': 'Please enter a valid email address (e.g. name@example.com).',
        }
    )

    address = forms.CharField(
        max_length=500,
        min_length=5,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Street address',
            'rows': 3,
        }),
        error_messages={
            'required': 'Please enter your address.',
            'min_length': 'Address must be at least 5 characters.',
        }
    )

    city = forms.CharField(
        max_length=100,
        min_length=2,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'City',
        }),
        error_messages={
            'required': 'Please enter your city.',
        }
    )

    postal_code = forms.CharField(
        max_length=20,
        min_length=3,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Postal code',
        }),
        error_messages={
            'required': 'Please enter your postal code.',
            'min_length': 'Postal code must be at least 3 characters.',
        }
    )

    def clean_full_name(self):
        name = self.cleaned_data.get('full_name', '').strip()
        dangerous = re.compile(
            r"(--|;|'|\"|<|>|script|select|insert|update|delete|drop|union|exec)",
            re.IGNORECASE
        )
        if dangerous.search(name):
            raise forms.ValidationError('Name contains invalid characters.')
        return name

    def clean_address(self):
        address = self.cleaned_data.get('address', '').strip()
        dangerous = re.compile(r"(<script|javascript:|on\w+=)", re.IGNORECASE)
        if dangerous.search(address):
            raise forms.ValidationError('Address contains invalid characters.')
        return address

    def clean_city(self):
        city = self.cleaned_data.get('city', '').strip()
        if not re.match(r'^[a-zA-Z\s\-\.]+$', city):
            raise forms.ValidationError('City may only contain letters, spaces, and hyphens.')
        return city

    def clean_postal_code(self):
        code = self.cleaned_data.get('postal_code', '').strip()
        if not re.match(r'^[a-zA-Z0-9\s\-]+$', code):
            raise forms.ValidationError('Postal code may only contain letters, numbers, spaces, and hyphens.')
        return code
