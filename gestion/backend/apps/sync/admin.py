from django.contrib import admin

from .models import SyncCursor


@admin.register(SyncCursor)
class SyncCursorAdmin(admin.ModelAdmin):
    list_display = ("campaign", "cursor", "updated_at")
    search_fields = ("campaign__code",)
    readonly_fields = ("updated_at",)
