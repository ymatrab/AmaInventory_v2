"""Helper for recording audit-log entries (CLAUDE.md §7).

Call ``record_audit`` from services/views whenever state changes. Keep it cheap
and never let auditing failures break the main action in the future — for now it
writes synchronously.
"""

from __future__ import annotations

from typing import Any

from .models import AuditLog


def record_audit(
    actor: Any,
    action: str,
    entity: str,
    entity_id: str | int = "",
    **meta: Any,
) -> AuditLog:
    """Record a state-changing action.

    ``actor`` may be a Django user, ``None``, or an AnonymousUser; only a real
    authenticated user is stored.
    """
    stored_actor = (
        actor if (actor is not None and getattr(actor, "is_authenticated", False)) else None
    )
    return AuditLog.objects.create(
        actor=stored_actor,
        action=action,
        entity=entity,
        entity_id=str(entity_id),
        meta=meta or {},
    )
