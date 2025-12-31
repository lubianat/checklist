from django.contrib import admin

from .models import Token


@admin.register(Token)
class TokenAdmin(admin.ModelAdmin):
    list_display = ("user", "expires_at")
    search_fields = ("user__username",)
