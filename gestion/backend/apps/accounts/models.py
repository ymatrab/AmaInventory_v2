from django.conf import settings
from django.db import models


class FieldUserProfile(models.Model):
    """Extra profile data for a gestion (Django) staff user."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    matricule = models.CharField(max_length=50, unique=True)

    def __str__(self) -> str:
        return f"{self.user.username} ({self.matricule})"


class FieldUser(models.Model):
    """A field worker who performs counts on the public app.

    Not a Django auth user — authenticated per-campaign via link + PIN
    (AgentCredential). Identified by matricule for KPI attribution.
    """

    class Role(models.TextChoices):
        AGENT = "AGENT", "Agent"
        WAREHOUSEMAN = "WAREHOUSEMAN", "Warehouseman"

    matricule = models.CharField(max_length=50, unique=True)
    full_name = models.CharField(max_length=200)
    role = models.CharField(max_length=20, choices=Role.choices)
    phone = models.CharField(max_length=40, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["full_name"]

    def __str__(self) -> str:
        return f"{self.full_name} [{self.matricule}]"


class AuditLog(models.Model):
    """Append-only record of every state-changing action on the gestion side."""

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_entries",
    )
    action = models.CharField(max_length=100)
    entity = models.CharField(max_length=100)
    entity_id = models.CharField(max_length=64, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    meta = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["entity", "entity_id"]),
            models.Index(fields=["-timestamp"]),
        ]

    def __str__(self) -> str:
        return f"{self.timestamp:%Y-%m-%d %H:%M} · {self.action} · {self.entity}#{self.entity_id}"
