from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator, MinLengthValidator
from django.urls import reverse
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    title = models.CharField(
        max_length=200,
        validators=[MinLengthValidator(2)],
        help_text="Product title (2-200 chars)"
    )
    description = models.TextField(
        max_length=2000,
        blank=True,
        help_text="Product description (max 2000 chars)"
    )
    short_description = models.CharField(
        max_length=250,
        blank=True,
        help_text="Short product summary for listing previews"
    )
    feature_bullets = models.TextField(
        blank=True,
        help_text="One feature or specification per line."
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text="Price in USD"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )
    image_url = models.URLField(
        max_length=500,
        blank=True,
        help_text="URL to product image"
    )
    thumbnail = models.URLField(
        max_length=500,
        blank=True,
        help_text="URL to product thumbnail"
    )
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text="Rating 0-5"
    )
    stock = models.PositiveIntegerField(default=0)
    brand = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['brand']),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('core:product', args=[self.pk])

    @property
    def feature_bullet_list(self):
        return [line.strip() for line in self.feature_bullets.splitlines() if line.strip()]

    def update_rating(self):
        """Recalculate rating from reviews."""
        reviews = self.reviews.all()
        if reviews.exists():
            from django.db.models import Avg
            avg = reviews.aggregate(avg=Avg('rating'))['avg']
            self.rating = round(avg, 2)
        else:
            self.rating = 0
        self.save(update_fields=['rating'])


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating 1-5"
    )
    title = models.CharField(max_length=200, blank=True)
    comment = models.TextField(max_length=2000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product', 'user')  # one review per user per product
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.product.title} ({self.rating}★)"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.product.update_rating()

    def delete(self, *args, **kwargs):
        product = self.product
        super().delete(*args, **kwargs)
        product.update_rating()


class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlists')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlisted_by')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.user.username} → {self.product.title}"


class ProductImage(models.Model):
    """Multiple images per product for a gallery view."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image_url = models.URLField(max_length=500)
    alt_text = models.CharField(max_length=200, blank=True)
    position = models.PositiveIntegerField(default=0, help_text="Display order (lower = first)")

    class Meta:
        ordering = ['position']

    def __str__(self):
        return f"Image {self.position} for {self.product.title}"


class Question(models.Model):
    """Customer questions on a product page."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='questions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Q: {self.text[:60]} — {self.user.username}"


class Answer(models.Model):
    """Answers to customer questions."""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='answers')
    text = models.TextField(max_length=2000)
    is_seller_answer = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_seller_answer', 'created_at']

    def __str__(self):
        return f"A: {self.text[:60]} — {self.user.username}"
