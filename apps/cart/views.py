from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from apps.products.models import Product
from .models import Cart, CartItem


def _get_cart(request):
    """Get or create cart for current user/session."""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        # Merge guest session cart into user cart on login
        session_key = request.session.session_key
        if session_key:
            try:
                session_cart = Cart.objects.get(session_key=session_key, user__isnull=True)
                for item in session_cart.items.all():
                    existing, created_item = CartItem.objects.get_or_create(
                        cart=cart,
                        product=item.product,
                        defaults={'quantity': item.quantity}
                    )
                    if not created_item and item.quantity > existing.quantity:
                        existing.quantity = item.quantity
                        existing.save()
                session_cart.delete()
            except Cart.DoesNotExist:
                pass
    else:
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key)
    return cart


def cart_view(request):
    cart = _get_cart(request)
    items = cart.items.select_related('product').all()
    return render(request, 'cart/cart.html', {
        'cart': cart,
        'items': items,
        'qty_range': range(1, 31),
    })


@require_POST
def add_to_cart(request, product_id):
    cart = _get_cart(request)
    product = get_object_or_404(Product, pk=product_id)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    # Reject out-of-stock products
    if product.stock <= 0:
        msg = f'"{product.title}" is currently out of stock.'
        if is_ajax:
            return JsonResponse({'success': False, 'message': msg})
        messages.error(request, msg)
        return redirect(request.META.get('HTTP_REFERER', '/'))

    # Validate quantity
    try:
        qty = int(request.POST.get('quantity', 1))
        if qty < 1:
            qty = 1
        if qty > 30:
            qty = 30
    except (ValueError, TypeError):
        qty = 1

    # Don't allow more than available stock
    if qty > product.stock:
        qty = product.stock

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': qty}
    )

    if not created:
        cart_item.quantity = qty
        cart_item.save()

    msg = f'Added "{product.title}" to your cart (Qty: {qty}).'

    if is_ajax:
        return JsonResponse({
            'success': True,
            'message': msg,
            'cart_count': cart.total_items,
        })

    messages.success(request, msg)
    return redirect(request.META.get('HTTP_REFERER', '/'))


@require_POST
def update_cart(request, item_id):
    cart = _get_cart(request)
    cart_item = get_object_or_404(CartItem, pk=item_id, cart=cart)

    try:
        qty = int(request.POST.get('quantity', 1))
        if qty < 1:
            qty = 1
        if qty > 30:
            qty = 30
    except (ValueError, TypeError):
        qty = 1

    if qty > cart_item.product.stock:
        qty = cart_item.product.stock
        messages.warning(request, f'Only {cart_item.product.stock} available.')

    cart_item.quantity = qty
    cart_item.save()
    return redirect('cart:cart')


@require_POST
def remove_from_cart(request, item_id):
    cart = _get_cart(request)
    cart_item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    product_title = cart_item.product.title
    cart_item.delete()
    messages.info(request, f'Removed "{product_title}" from your cart.')
    return redirect('cart:cart')
