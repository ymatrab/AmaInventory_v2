from django.contrib import admin

from .models import AgentCredential, Assignment, Campaign, CampaignWarehouse


class CampaignWarehouseInline(admin.TabularInline):
    model = CampaignWarehouse
    extra = 0


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "type",
        "trigger",
        "scope",
        "status",
        "open_at",
        "close_at",
        "created_at",
    )
    list_filter = ("status", "type", "trigger", "scope")
    search_fields = ("code",)
    inlines = [CampaignWarehouseInline]


@admin.register(CampaignWarehouse)
class CampaignWarehouseAdmin(admin.ModelAdmin):
    list_display = ("campaign", "warehouse")
    search_fields = ("campaign__code", "warehouse__whs_code")


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "campaign",
        "warehouse",
        "field_user",
        "confirmed",
        "confirmed_by",
        "confirmed_at",
    )
    list_filter = ("confirmed",)
    search_fields = ("campaign__code", "warehouse__whs_code", "field_user__matricule")


@admin.register(AgentCredential)
class AgentCredentialAdmin(admin.ModelAdmin):
    list_display = ("field_user", "campaign", "active", "expires_at", "created_at")
    list_filter = ("active",)
    search_fields = ("field_user__matricule", "campaign__code")
    readonly_fields = ("pin_hash", "token")
