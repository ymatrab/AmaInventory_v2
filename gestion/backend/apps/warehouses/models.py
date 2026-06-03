from django.db import models


class Warehouse(models.Model):
    """A depot / warehouse, identified by its SAP WHS code."""

    whs_code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=200)
    city = models.CharField(max_length=120, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["whs_code"]

    def __str__(self) -> str:
        return f"{self.whs_code} — {self.name}"
