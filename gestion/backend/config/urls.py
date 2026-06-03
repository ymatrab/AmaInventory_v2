"""Root URL configuration for the gestion backend.

Phase 0: admin + a public health/placeholder endpoint so the stack is verifiably
runnable. Domain API routes are added from Phase 1 onward.
"""

from django.contrib import admin
from django.http import JsonResponse
from django.urls import path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


def index(_request) -> JsonResponse:
    return JsonResponse({"service": "gestion", "status": "ok", "phase": 0, "docs": "/admin/"})


@api_view(["GET"])
@permission_classes([AllowAny])
def health(_request) -> Response:
    return Response({"service": "gestion", "status": "ok"})


urlpatterns = [
    path("", index, name="index"),
    path("admin/", admin.site.urls),
    path("api/health/", health, name="health"),
]
