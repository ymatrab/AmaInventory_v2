from __future__ import annotations

from rest_framework import serializers

from .models import CountLine


class CountLineSerializer(serializers.ModelSerializer):
    item_code = serializers.CharField(source="item.item_code", read_only=True)
    sku = serializers.CharField(source="item.sku", read_only=True)
    whs_code = serializers.CharField(source="count.warehouse.whs_code", read_only=True)
    counted_by = serializers.CharField(source="counted_by.matricule", default=None, read_only=True)
    is_recount = serializers.BooleanField(source="count.is_recount", read_only=True)

    class Meta:
        model = CountLine
        fields = [
            "id",
            "line_uid",
            "whs_code",
            "item_code",
            "sku",
            "qty_units",
            "qty_packs",
            "total_units",
            "counted_by",
            "is_recount",
            "flagged_for_recount",
            "version",
            "updated_at",
        ]
