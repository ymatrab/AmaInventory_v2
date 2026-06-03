"""DRF permission classes keyed on the gestion role groups."""

from __future__ import annotations

from rest_framework.permissions import BasePermission

from . import groups


class _InGroup(BasePermission):
    group_name: str = ""

    def has_permission(self, request, view) -> bool:
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (user.is_superuser or user.groups.filter(name=self.group_name).exists())
        )


class IsInventoryResponsible(_InGroup):
    group_name = groups.INVENTORY_RESPONSIBLE


class IsAudit(_InGroup):
    group_name = groups.AUDIT


class IsCDG(_InGroup):
    group_name = groups.CDG
