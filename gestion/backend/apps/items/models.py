from django.db import models


class Item(models.Model):
    """Item master / reference. Reference only — NEVER holds quantities.

    ``units_per_pack`` enables unit<->pack conversion during counting.
    """

    item_code = models.CharField(max_length=60)
    sku = models.CharField(max_length=60)
    description = models.CharField(max_length=300, blank=True)
    color_parfum = models.CharField(max_length=120, blank=True)
    base_unit = models.CharField(max_length=20, default="unit")
    units_per_pack = models.PositiveIntegerField(default=1)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["item_code", "sku"]
        constraints = [
            models.UniqueConstraint(fields=["item_code", "sku"], name="uniq_item_code_sku"),
        ]

    def __str__(self) -> str:
        label = f"{self.item_code}/{self.sku}"
        return f"{label} — {self.description}" if self.description else label
