from django.contrib import admin

from .models import Catalog, PassportStamp, VisitingList, VisitingPlace


@admin.register(Catalog)
class CatalogAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_by", "created_at")
    search_fields = ("name", "slug", "created_by__username")


@admin.register(VisitingList)
class VisitingListAdmin(admin.ModelAdmin):
    list_display = ("id", "catalog", "created_by", "created_at")
    search_fields = ("catalog__name", "created_by__username")


@admin.register(VisitingPlace)
class VisitingPlaceAdmin(admin.ModelAdmin):
    list_display = ("entity_id", "catalog", "label", "coord")
    search_fields = ("entity_id", "label", "description")
    list_filter = ("catalog",)


@admin.register(PassportStamp)
class PassportStampAdmin(admin.ModelAdmin):
    list_display = ("user", "place")
    search_fields = ("user__username", "place__entity_id")
