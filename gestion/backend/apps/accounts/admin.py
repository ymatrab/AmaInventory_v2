from django.contrib import admin

from .models import AuditLog, FieldUser, FieldUserProfile


@admin.register(FieldUserProfile)
class FieldUserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "matricule")
    search_fields = ("user__username", "matricule")


@admin.register(FieldUser)
class FieldUserAdmin(admin.ModelAdmin):
    list_display = ("matricule", "full_name", "role", "phone", "active")
    list_filter = ("role", "active")
    search_fields = ("matricule", "full_name")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "actor", "action", "entity", "entity_id")
    list_filter = ("action", "entity")
    search_fields = ("entity", "entity_id", "action")
    readonly_fields = ("actor", "action", "entity", "entity_id", "timestamp", "meta")

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False
