"""Live counts monitoring + agent KPI (read-only, from pulled data)."""

from __future__ import annotations

from django.db.models import Count as CountAgg
from django.db.models import Max
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import CountLine
from .serializers import CountLineSerializer


class CountLineViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = CountLineSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = CountLine.objects.select_related("item", "count__warehouse", "counted_by")
        params = self.request.query_params
        if params.get("campaign"):
            qs = qs.filter(count__campaign_id=params["campaign"])
        if params.get("warehouse"):
            qs = qs.filter(count__warehouse_id=params["warehouse"])
        if params.get("agent"):
            qs = qs.filter(counted_by__matricule=params["agent"])
        return qs

    @action(detail=False, methods=["get"])
    def monitor(self, request):
        """Per-warehouse progress for a campaign (lines, flagged, last update)."""
        campaign = request.query_params.get("campaign")
        rows = (
            CountLine.objects.filter(count__campaign_id=campaign)
            .values("count__warehouse__whs_code")
            .annotate(lines=CountAgg("id"), last_update=Max("updated_at"))
            .order_by("count__warehouse__whs_code")
        )
        flagged = (
            CountLine.objects.filter(count__campaign_id=campaign, flagged_for_recount=True)
            .values("count__warehouse__whs_code")
            .annotate(flagged=CountAgg("id"))
        )
        flagged_map = {f["count__warehouse__whs_code"]: f["flagged"] for f in flagged}
        data = [
            {
                "whs_code": r["count__warehouse__whs_code"],
                "lines": r["lines"],
                "flagged": flagged_map.get(r["count__warehouse__whs_code"], 0),
                "last_update": r["last_update"],
            }
            for r in rows
        ]
        return Response({"warehouses": data})

    @action(detail=False, methods=["get"])
    def kpi(self, request):
        """Per-agent KPI for a campaign: lines counted + total units."""
        from django.db.models import Sum

        campaign = request.query_params.get("campaign")
        rows = (
            CountLine.objects.filter(count__campaign_id=campaign, counted_by__isnull=False)
            .values("counted_by__matricule", "counted_by__full_name")
            .annotate(lines=CountAgg("id"), units=Sum("total_units"))
            .order_by("-lines")
        )
        return Response({"agents": list(rows)})
