from django.contrib import admin

from .models import Count, CountLine


class CountLineInline(admin.TabularInline):
    model = CountLine
    extra = 0
    readonly_fields = ("line_uid", "total_units", "version", "updated_at")


@admin.register(Count)
class CountAdmin(admin.ModelAdmin):
    list_display = (
        "campaign",
        "warehouse",
        "is_recount",
        "parent_count",
        "status",
        "synced_at",
        "created_at",
    )
    list_filter = ("is_recount", "status")
    search_fields = ("campaign__code", "warehouse__whs_code")
    inlines = [CountLineInline]


@admin.register(CountLine)
class CountLineAdmin(admin.ModelAdmin):
    list_display = (
        "count",
        "item",
        "qty_units",
        "qty_packs",
        "total_units",
        "counted_by",
        "flagged_for_recount",
        "version",
    )
    list_filter = ("flagged_for_recount",)
    search_fields = ("item__item_code", "line_uid")
    readonly_fields = ("line_uid", "total_units", "updated_at")
