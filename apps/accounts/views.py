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
