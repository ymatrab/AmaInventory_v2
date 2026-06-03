import uuid

from django.db import models


class Count(models.Model):
    """A count of a warehouse for a campaign (the local, pulled copy).

    A re-count is a copy of an original count (BR-08): ``is_recount=True`` with
    ``parent_count`` pointing at the original, which is preserved.
    """

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        SUBMITTED = "SUBMITTED", "Submitted"

    campaign = models.ForeignKey(
        "campaigns.Campaign", on_delete=models.CASCADE, related_name="counts"
    )
    warehouse = models.ForeignKey(
        "warehouses.Warehouse", on_delete=models.CASCADE, related_name="counts"
    )
    is_recount = models.BooleanField(default=False)
    parent_count = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="recounts"
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    synced_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        kind = "recount" if self.is_recount else "count"
        return f"{kind}:{self.campaign.code}/{self.warehouse.whs_code}"


class CountLine(models.Model):
    """A single counted item line, pulled from the public app.

    Idempotent sync key: ``line_uid`` + ``version`` (CLAUDE.md §7).
    ``total_units`` is derived from qty_units + qty_packs * item.units_per_pack.
    """

    count = models.ForeignKey(Count, on_delete=models.CASCADE, related_name="lines")
    item = models.ForeignKey("items.Item", on_delete=models.PROTECT, related_name="count_lines")
    qty_units = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    qty_packs = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    total_units = models.DecimalField(max_digits=16, decimal_places=3, default=0)
    counted_by = models.ForeignKey(
        "accounts.FieldUser",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="count_lines",
    )
    flagged_for_recount = models.BooleanField(default=False)
    line_uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    version = models.IntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["item__item_code"]
        indexes = [models.Index(fields=["line_uid", "version"])]

    def compute_total_units(self):
        per_pack = self.item.units_per_pack if self.item_id else 1
        return self.qty_units + self.qty_packs * per_pack

    def save(self, *args, **kwargs):
        self.total_units = self.compute_total_units()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.item.item_code} = {self.total_units}u (v{self.version})"
