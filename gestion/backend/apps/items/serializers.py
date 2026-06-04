from __future__ import annotations

from rest_framework import serializers

from .models import Item


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = [
            "id",
            "item_code",
            "sku",
            "description",
            "color_parfum",
            "base_unit",
            "units_per_pack",
            "active",
        ]
