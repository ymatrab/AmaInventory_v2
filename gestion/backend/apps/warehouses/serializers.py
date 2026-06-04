from __future__ import annotations

from rest_framework import serializers

from .models import Warehouse


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ["id", "whs_code", "name", "city", "active"]
