from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F
from decimal import Decimal
from apps.cart.views import _get_cart
from apps.products.models import Product
from .models import Order, OrderItem
from .forms import CheckoutForm


@login_required
def checkout(request):
    cart = _get_cart(request)
    items = cart.items.select_related('product').all()

    if not items:
        messages.warning(request, 'Your cart is empty.')
        return redirect('cart:cart')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # SECURITY FIX: Use select_for_update + F() to prevent race conditions
            with transaction.atomic():
                # Lock product rows to prevent concurrent overselling
                product_ids = [item.product_id for item in items]
                locked_products = {
                    p.pk: p for p in Product.objects.select_for_update().filter(pk__in=product_ids)
                }

                # Validate stock with locked rows
                stock_errors = []
                for item in items:
                    product = locked_products[item.product_id]
                    if product.stock <= 0:
                        stock_errors.append(f'"{product.title}" is now out of stock.')
                    elif item.quantity > product.stock:
                        stock_errors.append(
                            f'Only {product.stock} of "{product.title}" available '
                            f'(you requested {item.quantity}).'
                        )

                if stock_errors:
                    for err in stock_errors:
                        messages.error(request, err)
                    return render(request, 'orders/checkout.html', {
                        'form': form,
                        'cart': cart,
                        'items': items,
                    })

                # Recalculate total from actual locked prices
                calculated_total = Decimal('0.00')
                order_items_data = []

                for item in items:
                    product = locked_products[item.product_id]
                    line_total = product.price * item.quantity
                    calculated_total += line_total
                    order_items_data.append({
                        'product': product,
                        'product_title': product.title,
                        'price': product.price,
                        'quantity': item.quantity,
                    })

                order = Order.objects.create(
                    user=request.user,
                    full_name=form.cleaned_data['full_name'],
                    email=form.cleaned_data['email'],
                    address=form.cleaned_data['address'],
                    city=form.cleaned_data['city'],
                    postal_code=form.cleaned_data['postal_code'],
                    total_amount=calculated_total,
                )

                for data in order_items_data:
                    OrderItem.objects.create(order=order, **data)
                    # SECURITY FIX: Use F() expression for atomic stock deduction
                    Product.objects.filter(pk=data['product'].pk).update(
                        stock=F('stock') - data['quantity']
                    )

                # Ensure stock never goes negative (safety net)
                Product.objects.filter(pk__in=product_ids, stock__lt=0).update(stock=0)

                # Clear the cart
                cart.items.all().delete()

            messages.success(request, 'Your order has been placed successfully!')
            return redirect('orders:confirmation', order_id=order.pk)
    else:
        initial = {
            'email': request.user.email,
            'full_name': f"{request.user.first_name} {request.user.last_name}".strip(),
        }
        form = CheckoutForm(initial=initial)

    return render(request, 'orders/checkout.html', {
        'form': form,
        'cart': cart,
        'items': items,
    })


@login_required
def order_confirmation(request, order_id):
    """Only the order owner can view their confirmation — prevents IDOR."""
    order = get_object_or_404(Order, pk=order_id, user=request.user)
    return render(request, 'orders/confirmation.html', {'order': order})
