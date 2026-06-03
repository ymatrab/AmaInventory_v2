from django.contrib import admin

from .models import Item


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = (
        "item_code",
        "sku",
        "description",
        "color_parfum",
        "base_unit",
        "units_per_pack",
        "active",
    )
    list_filter = ("active", "base_unit")
    search_fields = ("item_code", "sku", "description", "color_parfum")
