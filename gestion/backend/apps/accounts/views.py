"""Accounts API: a whoami endpoint + a sample group-protected endpoint.

The CDG-only endpoint exists to prove group-based permissions are enforced
(Phase 1 acceptance). Domain endpoints arrive in later phases.
"""

from __future__ import annotations

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import IsCDG


class WhoAmIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        user = request.user
        return Response(
            {
                "username": user.get_username(),
                "is_superuser": user.is_superuser,
                "groups": list(user.groups.values_list("name", flat=True)),
            }
        )


class CdgOnlyView(APIView):
    """Sample endpoint reachable only by superusers or the CDG group."""

    permission_classes = [IsCDG]

    def get(self, request: Request) -> Response:
        return Response({"ok": True, "scope": "cdg"})
