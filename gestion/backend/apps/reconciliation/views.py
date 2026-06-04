"""Reconciliation workspace API (CDG): gaps, margins, re-count, CSV, sign-off."""

from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.campaigns.models import Campaign
from apps.warehouses.models import Warehouse

from .models import CsvExport, Reconciliation, SignOff
from .serializers import (
    CsvExportSerializer,
    ReconciliationSerializer,
    SignOffSerializer,
)
from .services import (
    build_reconciliation,
    flag_for_recount,
    generate_csv_export,
    set_value_margin,
)


class ReconciliationViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = ReconciliationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Reconciliation.objects.select_related("warehouse").prefetch_related("lines__item")
        campaign = self.request.query_params.get("campaign")
        return qs.filter(campaign=campaign) if campaign else qs

    def _campaign_warehouse(self, request):
        campaign = Campaign.objects.get(pk=request.data["campaign"])
        warehouse = Warehouse.objects.get(pk=request.data["warehouse"])
        return campaign, warehouse

    @action(detail=False, methods=["post"])
    def build(self, request):
        campaign, warehouse = self._campaign_warehouse(request)
        recon = build_reconciliation(campaign, warehouse, actor=request.user)
        return Response(ReconciliationSerializer(recon).data)

    @action(detail=False, methods=["post"])
    def set_margin(self, request):
        campaign, warehouse = self._campaign_warehouse(request)
        recon = set_value_margin(
            campaign, warehouse, request.data["value_margin"], actor=request.user
        )
        return Response(ReconciliationSerializer(recon).data)

    @action(detail=False, methods=["post"])
    def flag_recount(self, request):
        campaign, warehouse = self._campaign_warehouse(request)
        recount = flag_for_recount(
            campaign, warehouse, request.data.get("item_codes", []), actor=request.user
        )
        return Response({"ok": True, "recount_count_id": recount.pk})


class CsvExportViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = CsvExportSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = CsvExport.objects.select_related("warehouse")
        campaign = self.request.query_params.get("campaign")
        return qs.filter(campaign=campaign) if campaign else qs

    @action(detail=False, methods=["post"])
    def generate(self, request):
        campaign = Campaign.objects.get(pk=request.data["campaign"])
        warehouse = (
            Warehouse.objects.get(pk=request.data["warehouse"])
            if request.data.get("warehouse")
            else None
        )
        export = generate_csv_export(campaign, warehouse, actor=request.user)
        return Response(CsvExportSerializer(export).data)

    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        export = self.get_object()
        path = Path(settings.MEDIA_ROOT) / export.file_ref
        if not path.exists():
            raise Http404("Export file not found.")
        return FileResponse(
            open(path, "rb"), as_attachment=True, filename=path.name, content_type="text/csv"
        )


class SignOffViewSet(viewsets.ModelViewSet):
    serializer_class = SignOffSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = SignOff.objects.select_related("warehouse")
        campaign = self.request.query_params.get("campaign")
        return qs.filter(campaign=campaign) if campaign else qs
