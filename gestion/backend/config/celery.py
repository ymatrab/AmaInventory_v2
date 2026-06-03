"""Celery application for the gestion backend.

Used by the sync poller (Phase 4) and other background jobs. Broker/result
backend come from REDIS_URL. Beat schedule is registered in later phases.
"""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("gestion")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self) -> None:  # pragma: no cover - smoke task
    print(f"Request: {self.request!r}")
