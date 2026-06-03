from django.conf import settings
from django.db import models


class Campaign(models.Model):
    """An inventory campaign — the unit of work, launched by Audit or CDG."""

    class Type(models.TextChoices):
        MONTHLY = "MONTHLY", "Monthly"
        PERIOD = "PERIOD", "Period / ad-hoc"

    class Trigger(models.TextChoices):
        ROUTINE = "ROUTINE", "Routine"
        HIGH_GAP = "HIGH_GAP", "High gap"
        ANOMALY = "ANOMALY", "Anomaly"

    class Scope(models.TextChoices):
        ALL = "ALL", "All warehouses"
        SPECIFIC = "SPECIFIC", "Specific warehouses"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ARMED = "ARMED", "Armed"
        OPEN = "OPEN", "Open"
        RECOUNT = "RECOUNT", "Re-count"
        CLOSED = "CLOSED", "Closed"
        ARCHIVED = "ARCHIVED", "Archived"

    code = models.CharField(max_length=40, unique=True)
    type = models.CharField(max_length=10, choices=Type.choices, default=Type.MONTHLY)
    trigger = models.CharField(max_length=10, choices=Trigger.choices, default=Trigger.ROUTINE)
    scope = models.CharField(max_length=10, choices=Scope.choices, default=Scope.ALL)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    open_at = models.DateTimeField(null=True, blank=True)
    close_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_campaigns",
    )
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="confirmed_campaigns",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    warehouses = models.ManyToManyField(
        "warehouses.Warehouse", through="CampaignWarehouse", related_name="campaigns"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.code} ({self.get_status_display()})"


class CampaignWarehouse(models.Model):
    """Join table scoping a campaign to a warehouse."""

    campaign = models.ForeignKey(
        Campaign, on_delete=models.CASCADE, related_name="campaign_warehouses"
    )
    warehouse = models.ForeignKey("warehouses.Warehouse", on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["campaign", "warehouse"], name="uniq_campaign_warehouse"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.campaign.code} · {self.warehouse.whs_code}"


class Assignment(models.Model):
    """A field user assigned to count a warehouse for a campaign.

    Counting cannot start until Audit confirms the assignment list (BR-02).
    """

    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="assignments")
    warehouse = models.ForeignKey("warehouses.Warehouse", on_delete=models.CASCADE)
    field_user = models.ForeignKey(
        "accounts.FieldUser", on_delete=models.PROTECT, related_name="assignments"
    )
    confirmed = models.BooleanField(default=False)
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="confirmed_assignments",
    )
    confirmed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["campaign", "warehouse", "field_user"], name="uniq_assignment"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.campaign.code} · {self.warehouse.whs_code} · {self.field_user.matricule}"


class AgentCredential(models.Model):
    """Per-agent, per-campaign login pushed to the public app.

    Only the PIN *hash* is stored. Token + window bound the login (Phase 5).
    """

    field_user = models.ForeignKey(
        "accounts.FieldUser", on_delete=models.CASCADE, related_name="credentials"
    )
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="credentials")
    token = models.CharField(max_length=64, unique=True)
    pin_hash = models.CharField(max_length=255)
    active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["field_user", "campaign"], name="uniq_agent_credential"
            ),
        ]

    def __str__(self) -> str:
        return f"cred:{self.field_user.matricule}@{self.campaign.code}"
