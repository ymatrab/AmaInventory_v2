"""Seed demo data: role groups, one user per group, demo warehouses/items/field users.

Idempotent — safe to run repeatedly. Richer seed (campaign + SAP-mock gaps) lands
in Phase 9. Run via ``make seed``.
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts import groups as role_groups
from apps.accounts.models import FieldUser
from apps.items.models import Item
from apps.warehouses.models import Warehouse

User = get_user_model()

DEMO_PASSWORD = "demo12345"

DEMO_USERS = [
    ("inv_resp", role_groups.INVENTORY_RESPONSIBLE),
    ("audit", role_groups.AUDIT),
    ("cdg", role_groups.CDG),
]

DEMO_WAREHOUSES = [
    {"whs_code": "WH-CASA", "name": "Casablanca Depot", "city": "Casablanca"},
    {"whs_code": "WH-RABAT", "name": "Rabat Depot", "city": "Rabat"},
]

DEMO_ITEMS = [
    {
        "item_code": "ITM-001",
        "sku": "ITM-001-RED",
        "description": "Shampoo 500ml",
        "color_parfum": "Red",
        "units_per_pack": 12,
    },
    {
        "item_code": "ITM-001",
        "sku": "ITM-001-BLUE",
        "description": "Shampoo 500ml",
        "color_parfum": "Blue",
        "units_per_pack": 12,
    },
    {
        "item_code": "ITM-002",
        "sku": "ITM-002-VANILLA",
        "description": "Soap bar",
        "color_parfum": "Vanilla",
        "units_per_pack": 24,
    },
]

DEMO_FIELD_USERS = [
    {"matricule": "AG-1001", "full_name": "Agent Demo", "role": FieldUser.Role.AGENT},
    {"matricule": "WM-2001", "full_name": "Warehouseman Demo", "role": FieldUser.Role.WAREHOUSEMAN},
]


class Command(BaseCommand):
    help = "Seed demo groups, users, warehouses, items, and field users."

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        # Groups
        group_objs = {
            name: Group.objects.get_or_create(name=name)[0] for name in role_groups.ALL_GROUPS
        }
        self.stdout.write(f"Groups ensured: {', '.join(role_groups.ALL_GROUPS)}")

        # One demo user per group (staff so they can reach the admin).
        for username, group_name in DEMO_USERS:
            user, created = User.objects.get_or_create(
                username=username, defaults={"is_staff": True}
            )
            if created:
                user.set_password(DEMO_PASSWORD)
                user.is_staff = True
                user.save()
            user.groups.add(group_objs[group_name])
            self.stdout.write(
                f"  user {username} ({group_name}) {'created' if created else 'exists'}"
            )

        # Warehouses
        for wh in DEMO_WAREHOUSES:
            Warehouse.objects.get_or_create(whs_code=wh["whs_code"], defaults=wh)
        self.stdout.write(f"Warehouses ensured: {len(DEMO_WAREHOUSES)}")

        # Items
        for it in DEMO_ITEMS:
            Item.objects.get_or_create(item_code=it["item_code"], sku=it["sku"], defaults=it)
        self.stdout.write(f"Items ensured: {len(DEMO_ITEMS)}")

        # Field users
        for fu in DEMO_FIELD_USERS:
            FieldUser.objects.get_or_create(matricule=fu["matricule"], defaults=fu)
        self.stdout.write(f"Field users ensured: {len(DEMO_FIELD_USERS)}")

        self.stdout.write(self.style.SUCCESS(f"Demo seed complete. Demo password: {DEMO_PASSWORD}"))
