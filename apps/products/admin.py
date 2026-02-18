from django.contrib import admin
from .models import Category, Product, Review, Wishlist, ProductImage, Question, Answer


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image_url', 'alt_text', 'position')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'category', 'rating', 'stock', 'created_at')
    list_filter = ('category', 'brand')
    search_fields = ('title', 'description', 'brand')
    ordering = ('-created_at',)
    inlines = [ProductImageInline]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'title', 'created_at')
    list_filter = ('rating',)
    search_fields = ('product__title', 'user__username', 'comment')
    ordering = ('-created_at',)


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'added_at')
    search_fields = ('user__username', 'product__title')
    ordering = ('-added_at',)


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    fields = ('user', 'text', 'is_seller_answer')


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'text_short', 'created_at')
    search_fields = ('product__title', 'user__username', 'text')
    ordering = ('-created_at',)
    inlines = [AnswerInline]

    def text_short(self, obj):
        return obj.text[:80]
    text_short.short_description = 'Question'


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'position', 'alt_text')
    list_filter = ('product',)
    ordering = ('product', 'position')
