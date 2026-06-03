from django.urls import path

from .views import CdgOnlyView, WhoAmIView

urlpatterns = [
    path("whoami/", WhoAmIView.as_view(), name="whoami"),
    path("cdg-only/", CdgOnlyView.as_view(), name="cdg-only"),
]
