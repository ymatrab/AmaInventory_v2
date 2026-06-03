from django.contrib import admin

from .models import CsvExport, Reconciliation, ReconciliationLine, SignOff, SystemStock


@admin.register(SystemStock)
class SystemStockAdmin(admin.ModelAdmin):
    list_display = ("campaign", "warehouse", "item", "system_qty", "unit_value")
    list_filter = ("campaign", "warehouse")
    search_fields = ("item__item_code",)


class ReconciliationLineInline(admin.TabularInline):
    model = ReconciliationLine
    extra = 0


@admin.register(Reconciliation)
class ReconciliationAdmin(admin.ModelAdmin):
    list_display = ("campaign", "warehouse", "value_margin", "status", "set_by", "set_at")
    list_filter = ("status",)
    search_fields = ("campaign__code", "warehouse__whs_code")
    inlines = [ReconciliationLineInline]


@admin.register(SignOff)
class SignOffAdmin(admin.ModelAdmin):
    list_display = (
        "campaign",
        "warehouse",
        "agent_signed",
        "warehouseman_signed",
        "received",
        "received_at",
    )
    list_filter = ("received", "agent_signed", "warehouseman_signed")
    search_fields = ("campaign__code", "warehouse__whs_code")


@admin.register(CsvExport)
class CsvExportAdmin(admin.ModelAdmin):
    list_display = ("campaign", "warehouse", "generated_at", "file_ref")
    search_fields = ("campaign__code",)
