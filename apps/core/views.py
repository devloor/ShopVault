from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db.models import Q, Avg, Count
from apps.products.models import Product, Category, Review, Wishlist


def home(request):
    categories = Category.objects.prefetch_related('products').all()[:8]
    featured_products = Product.objects.filter(rating__gte=4).order_by('-rating')[:6]
    latest_products = Product.objects.order_by('-created_at')[:6]

    context = {
        'categories': categories,
        'featured_products': featured_products,
        'latest_products': latest_products,
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
    reviews = product.reviews.select_related('user').order_by('-created_at')
    review_stats = reviews.aggregate(
        avg=Avg('rating'),
        count=Count('id'),
    )

    # Check if current user already reviewed
    user_review = None
    user_has_reviewed = False
    in_wishlist = False
    if request.user.is_authenticated:
        user_review = reviews.filter(user=request.user).first()
        user_has_reviewed = user_review is not None
        in_wishlist = Wishlist.objects.filter(user=request.user, product=product).exists()

    return render(request, 'core/product.html', {
        'product': product,
        'related_products': related_products,
        'reviews': reviews,
        'review_stats': review_stats,
        'user_review': user_review,
        'user_has_reviewed': user_has_reviewed,
        'in_wishlist': in_wishlist,
    })


def search(request):
    query = request.GET.get('q', '').strip()
    category_slug = request.GET.get('cat', '')
    sort = request.GET.get('sort', 'relevance')

    results = Product.objects.all()

    if query:
        results = results.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(brand__icontains=query)
        )

    if category_slug:
        results = results.filter(category__slug=category_slug)

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

    paginator = Paginator(results, 20)
    page = request.GET.get('page')
    products = paginator.get_page(page)
    categories = Category.objects.all()

    return render(request, 'core/search.html', {
        'products': products,
        'query': query,
        'categories': categories,
        'selected_category': category_slug,
        'selected_sort': sort,
        'result_count': paginator.count,
        'is_paginated': products.has_other_pages(),
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
    return redirect(request.META.get('HTTP_REFERER', 'core:product'))


@login_required
def wishlist_view(request):
    items = Wishlist.objects.filter(user=request.user).select_related('product')
    return render(request, 'core/wishlist.html', {'items': items})


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
