import re
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.validators import RegexValidator, MinLengthValidator


# Validator: only alphanumeric, underscores, hyphens
username_validator = RegexValidator(
    regex=r'^[a-zA-Z0-9_\-]+$',
    message='Username may only contain letters, numbers, underscores, and hyphens.'
)


class SafeRegistrationForm(UserCreationForm):
    """Registration form with proper validation and error messages."""

    username = forms.CharField(
        max_length=30,
        min_length=3,
        validators=[username_validator],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username',
            'autocomplete': 'username',
        }),
        help_text='3-30 characters. Letters, digits, underscores, hyphens only.',
        error_messages={
            'required': 'Please enter a username.',
            'min_length': 'Username must be at least 3 characters.',
            'max_length': 'Username cannot exceed 30 characters.',
        }
    )

    email = forms.EmailField(
        max_length=254,
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email address',
            'autocomplete': 'email',
        }),
        error_messages={
            'required': 'Please enter your email address.',
            'invalid': 'Please enter a valid email address (e.g. name@example.com).',
        }
    )

    password1 = forms.CharField(
        label='Password',
        min_length=8,
        max_length=128,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'At least 8 characters',
            'autocomplete': 'new-password',
        }),
        help_text='Password must be at least 8 characters long.',
        error_messages={
            'required': 'Please enter a password.',
            'min_length': 'Password must be at least 8 characters long.',
        }
    )

    password2 = forms.CharField(
        label='Confirm Password',
        min_length=8,
        max_length=128,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password',
            'autocomplete': 'new-password',
        }),
        error_messages={
            'required': 'Please confirm your password.',
            'min_length': 'Password must be at least 8 characters long.',
        }
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        dangerous = re.compile(
            r"(--|;|'|\"|<|>|script|select|insert|update|delete|drop|union|exec)",
            re.IGNORECASE
        )
        if dangerous.search(username):
            raise forms.ValidationError('Username contains invalid characters.')
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if not email:
            raise forms.ValidationError('Please enter your email address.')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean_password1(self):
        password = self.cleaned_data.get('password1', '')
        if len(password) < 8:
            raise forms.ValidationError('Password must be at least 8 characters long.')
        if password.isdigit():
            raise forms.ValidationError('Password cannot be entirely numeric.')
        if password.lower() in ('password', '12345678', 'qwerty12', 'abcdefgh'):
            raise forms.ValidationError('This password is too common. Please choose a stronger one.')
        return password

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1', '')
        password2 = self.cleaned_data.get('password2', '')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Passwords do not match.')
        return password2


class SafeLoginForm(AuthenticationForm):
    """Login form with styled inputs and validation."""

    username = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username',
            'autocomplete': 'username',
        }),
        error_messages={
            'required': 'Please enter your username.',
        }
    )

    password = forms.CharField(
        max_length=128,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
            'autocomplete': 'current-password',
        }),
        error_messages={
            'required': 'Please enter your password.',
        }
    )

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        dangerous = re.compile(
            r"(--|;|'|\"|<|>|script|select|insert|update|delete|drop|union|exec)",
            re.IGNORECASE
        )
        if dangerous.search(username):
            raise forms.ValidationError('Username contains invalid characters.')
        return username


class UserProfileForm(forms.Form):
    """Form for editing user profile information."""
    first_name = forms.CharField(
        max_length=30, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'}),
    )
    last_name = forms.CharField(
        max_length=30, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'}),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
    )
    phone = forms.CharField(
        max_length=20, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number'}),
    )
    bio = forms.CharField(
        max_length=500, required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Tell us about yourself', 'rows': 3}),
    )
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )


class AddressForm(forms.Form):
    """Form for creating/editing a saved address."""
    label = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Home, Office'}),
    )
    full_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full name'}),
    )
    phone = forms.CharField(
        max_length=20, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number'}),
    )
    street_address = forms.CharField(
        max_length=500,
        widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Street address', 'rows': 2}),
    )
    city = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
    )
    state = forms.CharField(
        max_length=100, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State / Province'}),
    )
    postal_code = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Postal code'}),
    )
    country = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Country'}),
        initial='Nigeria',
    )
    is_default = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Set as default address',
    )

