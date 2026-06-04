from __future__ import annotations

from rest_framework import serializers

from .models import CsvExport, Reconciliation, ReconciliationLine, SignOff


class ReconciliationLineSerializer(serializers.ModelSerializer):
    item_code = serializers.CharField(source="item.item_code", read_only=True)
    sku = serializers.CharField(source="item.sku", read_only=True)

    class Meta:
        model = ReconciliationLine
        fields = [
            "id",
            "item_code",
            "sku",
            "physical_qty",
            "system_qty",
            "gap_qty",
            "physical_value",
            "system_value",
            "gap_value",
            "within_margin",
        ]


class ReconciliationSerializer(serializers.ModelSerializer):
    whs_code = serializers.CharField(source="warehouse.whs_code", read_only=True)
    lines = ReconciliationLineSerializer(many=True, read_only=True)

    class Meta:
        model = Reconciliation
        fields = [
            "id",
            "campaign",
            "warehouse",
            "whs_code",
            "value_margin",
            "set_at",
            "status",
            "lines",
        ]


class CsvExportSerializer(serializers.ModelSerializer):
    whs_code = serializers.CharField(source="warehouse.whs_code", default=None, read_only=True)

    class Meta:
        model = CsvExport
        fields = ["id", "campaign", "whs_code", "generated_at", "file_ref"]


class SignOffSerializer(serializers.ModelSerializer):
    whs_code = serializers.CharField(source="warehouse.whs_code", read_only=True)

    class Meta:
        model = SignOff
        fields = [
            "id",
            "campaign",
            "warehouse",
            "whs_code",
            "agent_signed",
            "warehouseman_signed",
            "received",
            "received_at",
        ]
