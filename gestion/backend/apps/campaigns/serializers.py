"""Serializers for campaigns, assignments, and credential results."""

from __future__ import annotations

from rest_framework import serializers

from apps.warehouses.models import Warehouse

from .models import Assignment, Campaign


class CampaignSerializer(serializers.ModelSerializer):
    warehouse_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        queryset=Warehouse.objects.all(),
        source="warehouses",
        required=False,
    )
    warehouses = serializers.SerializerMethodField()
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Campaign
        fields = [
            "id",
            "code",
            "type",
            "trigger",
            "scope",
            "status",
            "status_display",
            "open_at",
            "close_at",
            "created_at",
            "warehouses",
            "warehouse_ids",
        ]
        read_only_fields = ["status", "created_at"]

    def get_warehouses(self, campaign: Campaign) -> list[dict]:
        return [
            {"id": w.pk, "whs_code": w.whs_code, "name": w.name} for w in campaign.warehouses.all()
        ]


class AssignmentSerializer(serializers.ModelSerializer):
    matricule = serializers.CharField(source="field_user.matricule", read_only=True)
    full_name = serializers.CharField(source="field_user.full_name", read_only=True)
    whs_code = serializers.CharField(source="warehouse.whs_code", read_only=True)

    class Meta:
        model = Assignment
        fields = [
            "id",
            "campaign",
            "warehouse",
            "whs_code",
            "field_user",
            "matricule",
            "full_name",
            "confirmed",
            "confirmed_at",
        ]
        read_only_fields = ["confirmed", "confirmed_at"]
