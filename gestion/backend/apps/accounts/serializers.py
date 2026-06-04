"""Serializers for accounts: the current user, field users, and audit log."""

from __future__ import annotations

from rest_framework import serializers

from apps.accounts.groups import AUDIT, CDG, INVENTORY_RESPONSIBLE

from .models import AuditLog, FieldUser


class MeSerializer(serializers.Serializer):
    """The signed-in staff user + the role flags the SPA uses for nav gating."""

    username = serializers.CharField(source="get_username")
    is_superuser = serializers.BooleanField()
    groups = serializers.SerializerMethodField()
    is_cdg = serializers.SerializerMethodField()
    is_audit = serializers.SerializerMethodField()
    is_inventory_responsible = serializers.SerializerMethodField()

    def _names(self, user) -> set[str]:
        return set(user.groups.values_list("name", flat=True))

    def get_groups(self, user) -> list[str]:
        return sorted(self._names(user))

    def get_is_cdg(self, user) -> bool:
        return user.is_superuser or CDG in self._names(user)

    def get_is_audit(self, user) -> bool:
        return user.is_superuser or AUDIT in self._names(user)

    def get_is_inventory_responsible(self, user) -> bool:
        return user.is_superuser or INVENTORY_RESPONSIBLE in self._names(user)


class FieldUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = FieldUser
        fields = ["id", "matricule", "full_name", "role", "phone", "active"]


class AuditLogSerializer(serializers.ModelSerializer):
    actor = serializers.CharField(source="actor.get_username", default=None, read_only=True)

    class Meta:
        model = AuditLog
        fields = ["id", "actor", "action", "entity", "entity_id", "timestamp", "meta"]
