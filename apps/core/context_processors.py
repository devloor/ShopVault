from apps.products.models import Category


def global_categories(request):
    categories = Category.objects.order_by('name').all()
    return {'global_categories': categories}
