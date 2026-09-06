"""Risk API URL declarations."""
from django.urls import path
from .views import HighRiskZonesView, HistoricalEventsView, NearbyZonesView, ZoneDetailView
urlpatterns = [path("zones/nearby/", NearbyZonesView.as_view()), path("high-risk/", HighRiskZonesView.as_view()), path("history/", HistoricalEventsView.as_view()), path("zones/<int:zone_id>/", ZoneDetailView.as_view())]
