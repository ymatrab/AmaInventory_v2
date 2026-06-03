"""Consistent DRF error envelope: {"error": {"detail": ..., "code": ...}}."""

from __future__ import annotations

from rest_framework.views import exception_handler as drf_exception_handler


def api_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is None:
        return None

    detail = response.data
    code = getattr(exc, "default_code", None) or "error"
    response.data = {"error": {"code": code, "detail": detail}}
    return response
