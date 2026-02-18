"""Cart context processor — makes cart_count available in all templates."""
from django.db.models import Sum
from apps.cart.models import Cart


def cart_count(request):
    count = 0
    try:
        if request.user.is_authenticated:
            # PERF FIX: Use DB aggregation instead of Python loop (N+1 → 1 query)
            result = Cart.objects.filter(user=request.user).aggregate(
                total=Sum('items__quantity')
            )
            count = result['total'] or 0
        else:
            session_key = request.session.session_key
            if session_key:
                result = Cart.objects.filter(session_key=session_key).aggregate(
                    total=Sum('items__quantity')
                )
                count = result['total'] or 0
    except Exception:
        pass

    return {'cart_count': count}
