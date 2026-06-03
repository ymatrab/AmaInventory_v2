from django.conf import settings
from django.db import models


class SystemStock(models.Model):
    """Snapshot of SAP system stock for a campaign/warehouse/item.

    LOCAL ONLY — populated from the SAP mock at campaign arming (Phase 2).
    Never leaves the local zone (CLAUDE.md §2).
    """

    campaign = models.ForeignKey(
        "campaigns.Campaign", on_delete=models.CASCADE, related_name="system_stock"
    )
    warehouse = models.ForeignKey(
        "warehouses.Warehouse", on_delete=models.CASCADE, related_name="system_stock"
    )
    item = models.ForeignKey("items.Item", on_delete=models.PROTECT, related_name="system_stock")
    system_qty = models.DecimalField(max_digits=16, decimal_places=3, default=0)
    unit_value = models.DecimalField(max_digits=14, decimal_places=4, default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["campaign", "warehouse", "item"], name="uniq_system_stock"
            ),
        ]

    def __str__(self) -> str:
        return f"stock:{self.campaign.code}/{self.warehouse.whs_code}/{self.item.item_code}={self.system_qty}"


class Reconciliation(models.Model):
    """CDG reconciliation of a warehouse for a campaign.

    ``value_margin`` is monetary and set per warehouse by CDG (BR-06).
    """

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        COMPLETED = "COMPLETED", "Completed"

    campaign = models.ForeignKey(
        "campaigns.Campaign", on_delete=models.CASCADE, related_name="reconciliations"
    )
    warehouse = models.ForeignKey(
        "warehouses.Warehouse", on_delete=models.CASCADE, related_name="reconciliations"
    )
    value_margin = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    set_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reconciliations",
    )
    set_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["campaign", "warehouse"], name="uniq_reconciliation"),
        ]

    def __str__(self) -> str:
        return f"recon:{self.campaign.code}/{self.warehouse.whs_code}"


class ReconciliationLine(models.Model):
    """Per-item gap line: physical vs system, in qty and value."""

    reconciliation = models.ForeignKey(
        Reconciliation, on_delete=models.CASCADE, related_name="lines"
    )
    item = models.ForeignKey(
        "items.Item", on_delete=models.PROTECT, related_name="reconciliation_lines"
    )
    physical_qty = models.DecimalField(max_digits=16, decimal_places=3, default=0)
    system_qty = models.DecimalField(max_digits=16, decimal_places=3, default=0)
    gap_qty = models.DecimalField(max_digits=16, decimal_places=3, default=0)
    physical_value = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    system_value = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    gap_value = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    within_margin = models.BooleanField(default=False)

    class Meta:
        ordering = ["item__item_code"]

    def __str__(self) -> str:
        return f"{self.item.item_code} gap={self.gap_value}"


class SignOff(models.Model):
    """Manual paper sign-off record (legal requirement, BR-10)."""

    campaign = models.ForeignKey(
        "campaigns.Campaign", on_delete=models.CASCADE, related_name="signoffs"
    )
    warehouse = models.ForeignKey(
        "warehouses.Warehouse", on_delete=models.CASCADE, related_name="signoffs"
    )
    agent_signed = models.BooleanField(default=False)
    warehouseman_signed = models.BooleanField(default=False)
    document = models.FileField(upload_to="signoffs/", null=True, blank=True)
    received = models.BooleanField(default=False)
    received_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["campaign", "warehouse"], name="uniq_signoff"),
        ]

    def __str__(self) -> str:
        return f"signoff:{self.campaign.code}/{self.warehouse.whs_code}"


class CsvExport(models.Model):
    """A generated CSV export for separate SAP import (BR-09)."""

    campaign = models.ForeignKey(
        "campaigns.Campaign", on_delete=models.CASCADE, related_name="csv_exports"
    )
    warehouse = models.ForeignKey(
        "warehouses.Warehouse",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="csv_exports",
    )
    generated_at = models.DateTimeField(auto_now_add=True)
    file_ref = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-generated_at"]

    def __str__(self) -> str:
        return f"csv:{self.campaign.code}@{self.generated_at:%Y-%m-%d %H:%M}"
