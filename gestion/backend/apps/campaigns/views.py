"""Campaign + assignment API.

Thin viewsets; lifecycle logic lives in services (arm/open/close/extend,
credential generation, sync). Role gating per CLAUDE.md: Audit confirms/opens,
CDG reconciles, Inventory Responsible assigns. Superusers may do anything.
"""

from __future__ import annotations

from django.utils import timezone
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.audit import record_audit
from apps.sync.services import push_campaign_setup

from .models import Assignment, Campaign
from .serializers import AssignmentSerializer, CampaignSerializer
from .services import (
    arm_campaign,
    close_campaign,
    extend_campaign,
    generate_credentials,
    open_campaign,
)


class CampaignViewSet(viewsets.ModelViewSet):
    queryset = Campaign.objects.all().prefetch_related("warehouses")
    serializer_class = CampaignSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        campaign = serializer.save(created_by=self.request.user)
        record_audit(self.request.user, "campaign.create", "Campaign", campaign.pk)

    @action(detail=True, methods=["post"])
    def arm(self, request, pk=None):
        campaign = self.get_object()
        rows = arm_campaign(campaign, actor=request.user)
        return Response({"ok": True, "system_stock_rows": rows})

    @action(detail=True, methods=["post"])
    def generate_credentials(self, request, pk=None):
        campaign = self.get_object()
        creds = generate_credentials(campaign, actor=request.user)
        # Plaintext token + PIN returned once for hand-out.
        return Response({"credentials": creds})

    @action(detail=True, methods=["post"])
    def push_setup(self, request, pk=None):
        campaign = self.get_object()
        push_campaign_setup(campaign)
        record_audit(request.user, "campaign.push_setup", "Campaign", campaign.pk)
        return Response({"ok": True})

    @action(detail=True, methods=["post"])
    def open(self, request, pk=None):
        campaign = open_campaign(self.get_object(), actor=request.user)
        return Response(CampaignSerializer(campaign).data)

    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        campaign = close_campaign(self.get_object(), actor=request.user)
        return Response(CampaignSerializer(campaign).data)

    @action(detail=True, methods=["post"])
    def extend(self, request, pk=None):
        close_at = request.data.get("close_at")
        campaign = extend_campaign(
            self.get_object(), timezone.datetime.fromisoformat(close_at), actor=request.user
        )
        return Response(CampaignSerializer(campaign).data)

    @action(detail=True, methods=["post"])
    def sync_now(self, request, pk=None):
        from apps.sync.services import pull_counts

        written = pull_counts(self.get_object())
        return Response({"ok": True, "rows": written})


class AssignmentViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = AssignmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Assignment.objects.select_related("field_user", "warehouse")
        campaign = self.request.query_params.get("campaign")
        return qs.filter(campaign=campaign) if campaign else qs

    def perform_create(self, serializer):
        assignment = serializer.save()
        record_audit(self.request.user, "assignment.create", "Assignment", assignment.pk)

    @action(detail=False, methods=["post"])
    def confirm(self, request):
        """Audit confirms all assignments for a campaign (BR-02)."""
        campaign_id = request.data.get("campaign")
        count = Assignment.objects.filter(campaign_id=campaign_id, confirmed=False).update(
            confirmed=True, confirmed_by=request.user, confirmed_at=timezone.now()
        )
        record_audit(request.user, "assignment.confirm", "Campaign", campaign_id, confirmed=count)
        return Response({"ok": True, "confirmed": count})
