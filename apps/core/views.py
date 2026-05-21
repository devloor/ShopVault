from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.views.decorators.http import require_POST, require_GET
from django.http import JsonResponse
from django.db.models import Q, Avg, Count, Sum, F
from django.utils import timezone
from datetime import timedelta
from apps.products.models import Product, Category, Review, Wishlist, Question, Answer


def home(request):
    categories = Category.objects.prefetch_related('products').all()[:8]
    featured_products = Product.objects.filter(rating__gte=4).order_by('-rating')[:6]
    latest_products = Product.objects.order_by('-created_at')[:6]

    # Recently viewed products (from session)
    recently_viewed_ids = request.session.get('recently_viewed', [])
    recently_viewed = []
    if recently_viewed_ids:
        products_map = Product.objects.in_bulk(recently_viewed_ids)
        recently_viewed = [products_map[pid] for pid in recently_viewed_ids if pid in products_map]

    context = {
        'categories': categories,
        'featured_products': featured_products,
        'latest_products': latest_products,
        'recently_viewed': recently_viewed,
    }
    return render(request, 'core/home.html', context)


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    product_list = Product.objects.filter(category=category).order_by('-rating')
    paginator = Paginator(product_list, 20)
    page = request.GET.get('page')
    products = paginator.get_page(page)
    return render(request, 'core/category.html', {
        'category': category,
        'products': products,
        'is_paginated': products.has_other_pages(),
    })


def product_detail(request, pk):
    product = get_object_or_404(Product.objects.select_related('category'), pk=pk)
    related_products = Product.objects.filter(
        category=product.category
    ).exclude(pk=product.pk).order_by('-rating')[:4]

    review_sort = request.GET.get('review_sort', 'recent')
    min_rating = request.GET.get('min_rating', '')
    reviews = product.reviews.select_related('user')

    if min_rating.isdigit():
        reviews = reviews.filter(rating__gte=int(min_rating))

    if review_sort == 'rating_high':
        reviews = reviews.order_by('-rating', '-created_at')
    elif review_sort == 'rating_low':
        reviews = reviews.order_by('rating', '-created_at')
    else:
        reviews = reviews.order_by('-created_at')

    review_stats = reviews.aggregate(
        avg=Avg('rating'),
        count=Count('id'),
    )

    # Image gallery
    gallery_images = product.images.all()

    # Q&A
    questions = product.questions.select_related('user').prefetch_related('answers__user').all()[:10]

    # Check if current user already reviewed
    user_review = None
    user_has_reviewed = False
    in_wishlist = False
    if request.user.is_authenticated:
        user_review = product.reviews.filter(user=request.user).first()
        user_has_reviewed = user_review is not None
        in_wishlist = Wishlist.objects.filter(user=request.user, product=product).exists()

    # Track recently viewed (session-based, max 10)
    viewed = request.session.get('recently_viewed', [])
    if pk in viewed:
        viewed.remove(pk)
    viewed.insert(0, pk)
    request.session['recently_viewed'] = viewed[:10]

    return render(request, 'core/product.html', {
        'product': product,
        'related_products': related_products,
        'reviews': reviews,
        'review_stats': review_stats,
        'review_sort': review_sort,
        'min_rating': min_rating,
        'user_review': user_review,
        'user_has_reviewed': user_has_reviewed,
        'in_wishlist': in_wishlist,
        'gallery_images': gallery_images,
        'questions': questions,
    })


def search(request):
    query = request.GET.get('q', '').strip()
    category_slug = request.GET.get('cat', '')
    sort = request.GET.get('sort', 'relevance')
    # Advanced filters
    price_min = request.GET.get('price_min', '')
    price_max = request.GET.get('price_max', '')
    brand_filter = request.GET.getlist('brand')
    rating_filter = request.GET.get('rating', '')
    in_stock = request.GET.get('in_stock', '')

    results = Product.objects.all()

    if query:
        results = results.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(brand__icontains=query)
        )

    if category_slug:
        results = results.filter(category__slug=category_slug)

    # Price range filter
    if price_min:
        try:
            results = results.filter(price__gte=float(price_min))
        except ValueError:
            pass
    if price_max:
        try:
            results = results.filter(price__lte=float(price_max))
        except ValueError:
            pass

    # Brand filter
    if brand_filter:
        results = results.filter(brand__in=brand_filter)

    # Rating filter
    if rating_filter:
        try:
            results = results.filter(rating__gte=int(rating_filter))
        except ValueError:
            pass

    # In-stock filter
    if in_stock == '1':
        results = results.filter(stock__gt=0)

    # Sorting
    if sort == 'price_low':
        results = results.order_by('price')
    elif sort == 'price_high':
        results = results.order_by('-price')
    elif sort == 'rating':
        results = results.order_by('-rating')
    elif sort == 'newest':
        results = results.order_by('-created_at')
    else:
        results = results.order_by('-rating')  # relevance default

    # Get available brands for filter sidebar
    all_brands = Product.objects.values_list('brand', flat=True).distinct().order_by('brand')
    all_brands = [b for b in all_brands if b]  # Remove empty

    paginator = Paginator(results, 20)
    page = request.GET.get('page')
    products = paginator.get_page(page)
    categories = Category.objects.annotate(product_count=Count('products'))

    return render(request, 'core/search.html', {
        'products': products,
        'query': query,
        'categories': categories,
        'selected_category': category_slug,
        'selected_sort': sort,
        'result_count': paginator.count,
        'is_paginated': products.has_other_pages(),
        # Advanced filter state
        'price_min': price_min,
        'price_max': price_max,
        'brand_filter': brand_filter,
        'all_brands': all_brands,
        'rating_filter': rating_filter,
        'in_stock': in_stock,
    })


@login_required
@require_POST
def add_review(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if Review.objects.filter(product=product, user=request.user).exists():
        messages.warning(request, 'You have already reviewed this product.')
        return redirect('core:product', pk=pk)

    if request.method == 'POST':
        try:
            rating = int(request.POST.get('rating', 5))
            rating = max(1, min(5, rating))
        except (ValueError, TypeError):
            rating = 5

        title = request.POST.get('review_title', '').strip()[:200]
        comment = request.POST.get('comment', '').strip()[:2000]

        Review.objects.create(
            product=product,
            user=request.user,
            rating=rating,
            title=title,
            comment=comment,
        )
        messages.success(request, 'Your review has been submitted!')

    return redirect('core:product', pk=pk)


@login_required
@require_POST
def delete_review(request, pk):
    review = get_object_or_404(Review, pk=pk, user=request.user)
    product_pk = review.product.pk
    review.delete()
    messages.info(request, 'Your review has been deleted.')
    return redirect('core:product', pk=product_pk)


@login_required
@require_POST
def toggle_wishlist(request, pk):
    product = get_object_or_404(Product, pk=pk)
    wish, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    if not created:
        wish.delete()
        messages.info(request, f'Removed "{product.title}" from your wishlist.')
    else:
        messages.success(request, f'Added "{product.title}" to your wishlist.')
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'in_wishlist': created,
            'button_label': '♥ In Wishlist' if created else '♡ Add to Wishlist',
            'message': ('Added' if created else 'Removed') + f' "{product.title}" from your wishlist.',
        })
    return redirect(request.META.get('HTTP_REFERER', 'core:product'))


@login_required
@require_GET
def search_suggestions(request):
    query = request.GET.get('q', '').strip()
    suggestions = []
    if query:
        matches = Product.objects.filter(
            Q(title__icontains=query) | Q(brand__icontains=query)
        ).order_by('-rating', 'title')[:8]
        suggestions = [
            {
                'title': p.title,
                'url': p.get_absolute_url(),
                'brand': p.brand,
                'price': str(p.price),
            }
            for p in matches
        ]
    return JsonResponse({'suggestions': suggestions})


@login_required
def wishlist_view(request):
    items = Wishlist.objects.filter(user=request.user).select_related('product')
    return render(request, 'core/wishlist.html', {'items': items})


# ========== Product Q&A ==========

@login_required
@require_POST
def ask_question(request, pk):
    """Post a question on a product page."""
    product = get_object_or_404(Product, pk=pk)
    text = request.POST.get('question_text', '').strip()[:1000]
    if text:
        Question.objects.create(product=product, user=request.user, text=text)
        messages.success(request, 'Your question has been posted!')
    else:
        messages.warning(request, 'Please enter a question.')
    return redirect('core:product', pk=pk)


@login_required
@require_POST
def answer_question(request, question_pk):
    """Answer a question on a product page."""
    question = get_object_or_404(Question.objects.select_related('product'), pk=question_pk)
    text = request.POST.get('answer_text', '').strip()[:2000]
    if text:
        Answer.objects.create(
            question=question,
            user=request.user,
            text=text,
            is_seller_answer=request.user.is_staff,
        )
        messages.success(request, 'Your answer has been posted!')
    else:
        messages.warning(request, 'Please enter an answer.')
    return redirect('core:product', pk=question.product.pk)


# ========== Admin Analytics Dashboard ==========

@staff_member_required
def admin_dashboard(request):
    """Staff-only analytics dashboard."""
    from apps.orders.models import Order
    from django.contrib.auth.models import User

    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Revenue stats
    total_revenue = Order.objects.aggregate(total=Sum('total_amount'))['total'] or 0
    month_revenue = Order.objects.filter(created_at__gte=month_start).aggregate(total=Sum('total_amount'))['total'] or 0
    today_revenue = Order.objects.filter(created_at__gte=today_start).aggregate(total=Sum('total_amount'))['total'] or 0

    # Order counts by status
    status_counts = dict(Order.objects.values_list('status').annotate(c=Count('id')).order_by('status'))

    # Total orders
    total_orders = Order.objects.count()

    # Top selling products (by order items quantity)
    from apps.orders.models import OrderItem
    top_products = OrderItem.objects.values('product_title').annotate(
        total_sold=Sum('quantity')
    ).order_by('-total_sold')[:5]

    # New users this month
    new_users_month = User.objects.filter(date_joined__gte=month_start).count()
    total_users = User.objects.count()

    # Revenue chart (last 30 days)
    revenue_by_day = []
    for i in range(29, -1, -1):
        day = (now - timedelta(days=i)).date()
        day_start = timezone.make_aware(timezone.datetime.combine(day, timezone.datetime.min.time()))
        day_end = day_start + timedelta(days=1)
        day_revenue = Order.objects.filter(
            created_at__gte=day_start, created_at__lt=day_end
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        revenue_by_day.append({
            'date': day.strftime('%b %d'),
            'revenue': float(day_revenue),
        })

    # Recent orders
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:10]

    import json
    context = {
        'total_revenue': total_revenue,
        'month_revenue': month_revenue,
        'today_revenue': today_revenue,
        'total_orders': total_orders,
        'status_counts': status_counts,
        'top_products': top_products,
        'new_users_month': new_users_month,
        'total_users': total_users,
        'revenue_by_day_json': json.dumps(revenue_by_day),
        'recent_orders': recent_orders,
    }
    return render(request, 'core/admin_dashboard.html', context)


def deals(request):
    deal_list = Product.objects.filter(stock__gt=0, rating__gte=3).order_by('price')
    paginator = Paginator(deal_list, 24)
    page = request.GET.get('page')
    products = paginator.get_page(page)
    return render(request, 'core/deals.html', {
        'products': products,
        'is_paginated': products.has_other_pages(),
    })


def customer_service(request):
    return render(request, 'core/customer_service.html')


def gift_cards(request):
    return render(request, 'core/gift_cards.html')


def sell(request):
    return render(request, 'core/sell.html')


def about(request):
    return render(request, 'core/about.html')


def careers(request):
    return render(request, 'core/careers.html')


def advertise(request):
    return render(request, 'core/advertise.html')


def conditions(request):
    return render(request, 'core/conditions.html')


def privacy(request):
    return render(request, 'core/privacy.html')
