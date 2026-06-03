from django.contrib import admin

from .models import Warehouse


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ("whs_code", "name", "city", "active")
    list_filter = ("active", "city")
    search_fields = ("whs_code", "name", "city")
