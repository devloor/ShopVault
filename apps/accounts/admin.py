from django.contrib import admin
from .models import UserProfile, Address


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    fields = ('phone', 'bio', 'date_of_birth', 'avatar_url')


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'label', 'full_name', 'city', 'country', 'is_default')
    list_filter = ('is_default', 'country')
    search_fields = ('user__username', 'full_name', 'city')
    ordering = ('user', '-is_default')
