"""Celery tasks for the pull poller. Gestion is the only initiator."""

from __future__ import annotations

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def poll_open_campaigns() -> int:
    """Beat task: pull counts for every OPEN/RECOUNT campaign. Returns rows written."""
    from apps.campaigns.models import Campaign

    from .services import pull_counts

    total = 0
    statuses = [Campaign.Status.OPEN, Campaign.Status.RECOUNT]
    for campaign in Campaign.objects.filter(status__in=statuses):
        try:
            total += pull_counts(campaign)
        except Exception:  # noqa: BLE001 - one campaign must not break the poll loop
            logger.exception("pull_counts failed for campaign %s", campaign.pk)
    return total


@shared_task
def pull_counts_task(campaign_id: int) -> int:
    """On-demand pull for a single campaign (used by the 'Sync now' action)."""
    from apps.campaigns.models import Campaign

    from .services import pull_counts

    return pull_counts(Campaign.objects.get(pk=campaign_id))
