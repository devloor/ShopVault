import time
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, login, authenticate
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils.http import url_has_allowed_host_and_scheme
from django.core.paginator import Paginator
from .forms import SafeRegistrationForm, SafeLoginForm
from apps.orders.models import Order


# Rate limiting constants
MAX_LOGIN_ATTEMPTS = 5
LOGIN_COOLDOWN_SECONDS = 300  # 5 minutes


@login_required
def dashboard(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
    return render(request, 'accounts/dashboard.html', {
        'orders': orders,
    })


@login_required
def order_history(request):
    order_list = Order.objects.filter(user=request.user).order_by('-created_at')
    paginator = Paginator(order_list, 10)
    page = request.GET.get('page')
    orders = paginator.get_page(page)
    return render(request, 'accounts/order_history.html', {
        'orders': orders,
        'is_paginated': orders.has_other_pages(),
    })


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, pk=order_id, user=request.user)
    return render(request, 'accounts/order_detail.html', {'order': order})


@require_POST
def logout_view(request):
    """Logout requires POST to prevent CSRF logout attacks."""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('core:home')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    # --- Rate limiting ---
    attempts = request.session.get('login_attempts', 0)
    lockout_until = request.session.get('login_lockout_until', 0)

    if lockout_until and time.time() < lockout_until:
        remaining = int(lockout_until - time.time())
        minutes = remaining // 60
        seconds = remaining % 60
        messages.error(
            request,
            f'Too many failed attempts. Please try again in {minutes}m {seconds}s.'
        )
        return render(request, 'accounts/login.html', {
            'form': SafeLoginForm(),
            'next': request.GET.get('next', ''),
            'locked_out': True,
        })

    if request.method == 'POST':
        form = SafeLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)

                # SECURITY FIX: Rotate session to prevent session fixation
                request.session.cycle_key()

                # Reset rate limiting on success
                request.session.pop('login_attempts', None)
                request.session.pop('login_lockout_until', None)

                messages.info(request, f"You are now logged in as {username}.")

                # Safe redirect: only allow internal URLs
                next_url = request.POST.get('next', request.GET.get('next', ''))
                if next_url and url_has_allowed_host_and_scheme(
                    next_url,
                    allowed_hosts={request.get_host()},
                    require_https=request.is_secure(),
                ):
                    return redirect(next_url)
                return redirect('core:home')
            else:
                # Increment failed attempts
                attempts += 1
                request.session['login_attempts'] = attempts
                if attempts >= MAX_LOGIN_ATTEMPTS:
                    request.session['login_lockout_until'] = time.time() + LOGIN_COOLDOWN_SECONDS
                    messages.error(
                        request,
                        f'Too many failed attempts. Account locked for {LOGIN_COOLDOWN_SECONDS // 60} minutes.'
                    )
                else:
                    remaining = MAX_LOGIN_ATTEMPTS - attempts
                    messages.error(
                        request,
                        f"Invalid username or password. {remaining} attempt(s) remaining."
                    )
        else:
            attempts += 1
            request.session['login_attempts'] = attempts
            if attempts >= MAX_LOGIN_ATTEMPTS:
                request.session['login_lockout_until'] = time.time() + LOGIN_COOLDOWN_SECONDS
                messages.error(
                    request,
                    f'Too many failed attempts. Account locked for {LOGIN_COOLDOWN_SECONDS // 60} minutes.'
                )
            else:
                remaining = MAX_LOGIN_ATTEMPTS - attempts
                messages.error(
                    request,
                    f"Invalid username or password. {remaining} attempt(s) remaining."
                )
    else:
        form = SafeLoginForm()

    return render(request, 'accounts/login.html', {
        'form': form,
        'next': request.GET.get('next', ''),
    })


def register_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    if request.method == 'POST':
        form = SafeRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)

            # SECURITY FIX: Rotate session after registration+login too
            request.session.cycle_key()

            messages.success(request, "Registration successful. Welcome!")
            return redirect('accounts:dashboard')
        messages.error(request, "Please correct the errors below.")
    else:
        form = SafeRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def password_change(request):
    from django.contrib.auth.forms import PasswordChangeForm
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password has been changed successfully.')
            return redirect('accounts:dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)

    # Style the form fields
    for field_name in form.fields:
        form.fields[field_name].widget.attrs.update({'class': 'form-control'})

    return render(request, 'accounts/password_change.html', {'form': form})


@login_required
def profile_view(request):
    """View and edit user profile."""
    from .models import UserProfile
    from .forms import UserProfileForm

    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST)
        if form.is_valid():
            # Update User fields
            request.user.first_name = form.cleaned_data['first_name']
            request.user.last_name = form.cleaned_data['last_name']
            request.user.email = form.cleaned_data['email']
            request.user.save()
            # Update Profile fields
            profile.phone = form.cleaned_data['phone']
            profile.bio = form.cleaned_data['bio']
            profile.date_of_birth = form.cleaned_data['date_of_birth']
            profile.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(initial={
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
            'phone': profile.phone,
            'bio': profile.bio,
            'date_of_birth': profile.date_of_birth,
        })

    return render(request, 'accounts/profile.html', {'form': form, 'profile': profile})


@login_required
def address_list(request):
    """List all saved addresses."""
    from .models import Address
    addresses = Address.objects.filter(user=request.user)
    return render(request, 'accounts/addresses.html', {'addresses': addresses})


@login_required
def address_create(request):
    """Create a new address."""
    from .models import Address
    from .forms import AddressForm

    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            Address.objects.create(
                user=request.user,
                label=form.cleaned_data['label'],
                full_name=form.cleaned_data['full_name'],
                phone=form.cleaned_data['phone'],
                street_address=form.cleaned_data['street_address'],
                city=form.cleaned_data['city'],
                state=form.cleaned_data['state'],
                postal_code=form.cleaned_data['postal_code'],
                country=form.cleaned_data['country'],
                is_default=form.cleaned_data['is_default'],
            )
            messages.success(request, 'Address added successfully.')
            return redirect('accounts:addresses')
    else:
        form = AddressForm()

    return render(request, 'accounts/address_form.html', {'form': form, 'title': 'Add New Address'})


@login_required
def address_edit(request, address_id):
    """Edit existing address."""
    from .models import Address
    from .forms import AddressForm

    address = get_object_or_404(Address, pk=address_id, user=request.user)

    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address.label = form.cleaned_data['label']
            address.full_name = form.cleaned_data['full_name']
            address.phone = form.cleaned_data['phone']
            address.street_address = form.cleaned_data['street_address']
            address.city = form.cleaned_data['city']
            address.state = form.cleaned_data['state']
            address.postal_code = form.cleaned_data['postal_code']
            address.country = form.cleaned_data['country']
            address.is_default = form.cleaned_data['is_default']
            address.save()
            messages.success(request, 'Address updated successfully.')
            return redirect('accounts:addresses')
    else:
        form = AddressForm(initial={
            'label': address.label,
            'full_name': address.full_name,
            'phone': address.phone,
            'street_address': address.street_address,
            'city': address.city,
            'state': address.state,
            'postal_code': address.postal_code,
            'country': address.country,
            'is_default': address.is_default,
        })

    return render(request, 'accounts/address_form.html', {'form': form, 'title': 'Edit Address', 'address': address})


@login_required
@require_POST
def address_delete(request, address_id):
    """Delete an address."""
    from .models import Address
    address = get_object_or_404(Address, pk=address_id, user=request.user)
    address.delete()
    messages.success(request, 'Address deleted.')
    return redirect('accounts:addresses')

