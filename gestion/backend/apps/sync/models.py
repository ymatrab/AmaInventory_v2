from django.db import models


class SyncCursor(models.Model):
    """Per-campaign pull cursor for the public -> gestion count sync.

    Stores the opaque cursor string returned by the public sync API
    (``updated_at|line_uid``) so polling resumes where it left off.
    """

    campaign = models.OneToOneField(
        "campaigns.Campaign", on_delete=models.CASCADE, related_name="sync_cursor"
    )
    cursor = models.CharField(max_length=128, blank=True, default="")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"cursor:{self.campaign.code}={self.cursor or '∅'}"
