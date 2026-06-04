"""Accounts API: session auth (csrf/login/logout/me), field users, audit log.

Session auth + Django Groups (CLAUDE.md §3). The SPA fetches the CSRF cookie,
then logs in with username/password; subsequent unsafe requests carry the
X-CSRFToken header. All endpoints are local-zone/VPN only.
"""

from __future__ import annotations

from django.contrib.auth import authenticate, login, logout
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AuditLog, FieldUser
from .permissions import IsCDG
from .serializers import AuditLogSerializer, FieldUserSerializer, MeSerializer


@method_decorator(ensure_csrf_cookie, name="get")
class CsrfView(APIView):
    """GET to receive the csrftoken cookie before logging in."""

    permission_classes = []

    def get(self, request: Request) -> Response:
        return Response({"detail": "CSRF cookie set."})


class LoginView(APIView):
    permission_classes = []

    def post(self, request: Request) -> Response:
        user = authenticate(
            request,
            username=request.data.get("username"),
            password=request.data.get("password"),
        )
        if user is None:
            return Response(
                {"error": {"code": "invalid_login", "detail": "Invalid credentials."}},
                status=401,
            )
        login(request, user)
        return Response(MeSerializer(user).data)


class LogoutView(APIView):
    def post(self, request: Request) -> Response:
        logout(request)
        return Response({"ok": True})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        return Response(MeSerializer(request.user).data)


class CdgOnlyView(APIView):
    """Sample endpoint reachable only by superusers or the CDG group (Phase 1)."""

    permission_classes = [IsCDG]

    def get(self, request: Request) -> Response:
        return Response({"ok": True, "scope": "cdg"})


class FieldUserViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Read-only list of field users (for assignment dropdowns)."""

    queryset = FieldUser.objects.all()
    serializer_class = FieldUserSerializer


class AuditLogViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Read-only audit history; filter by ``?entity=&entity_id=``."""

    serializer_class = AuditLogSerializer

    def get_queryset(self):
        qs = AuditLog.objects.all()
        entity = self.request.query_params.get("entity")
        entity_id = self.request.query_params.get("entity_id")
        if entity:
            qs = qs.filter(entity=entity)
        if entity_id:
            qs = qs.filter(entity_id=entity_id)
        return qs
