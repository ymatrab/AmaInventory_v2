"""Aggregated gestion API routes (mounted at /api/).

Session auth endpoints + a DRF router for every domain viewset the SPA consumes.
"""

from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.campaigns.views import AssignmentViewSet, CampaignViewSet
from apps.counts.views import CountLineViewSet
from apps.items.views import ItemViewSet
from apps.reconciliation.views import (
    CsvExportViewSet,
    ReconciliationViewSet,
    SignOffViewSet,
)
from apps.warehouses.views import WarehouseViewSet

from .views import (
    AuditLogViewSet,
    CdgOnlyView,
    CsrfView,
    FieldUserViewSet,
    LoginView,
    LogoutView,
    MeView,
)

router = DefaultRouter()
router.register("campaigns", CampaignViewSet, basename="campaign")
router.register("assignments", AssignmentViewSet, basename="assignment")
router.register("warehouses", WarehouseViewSet, basename="warehouse")
router.register("items", ItemViewSet, basename="item")
router.register("field-users", FieldUserViewSet, basename="field-user")
router.register("counts", CountLineViewSet, basename="count")
router.register("reconciliations", ReconciliationViewSet, basename="reconciliation")
router.register("exports", CsvExportViewSet, basename="export")
router.register("signoffs", SignOffViewSet, basename="signoff")
router.register("audit", AuditLogViewSet, basename="audit")

urlpatterns = [
    path("auth/csrf/", CsrfView.as_view(), name="csrf"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/me/", MeView.as_view(), name="me"),
    # Backward-compatible Phase 1 endpoints.
    path("whoami/", MeView.as_view(), name="whoami"),
    path("cdg-only/", CdgOnlyView.as_view(), name="cdg-only"),
    path("", include(router.urls)),
]
