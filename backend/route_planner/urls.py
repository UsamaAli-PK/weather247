from django.urls import path
from . import views

urlpatterns = [
    path("routes/", views.RouteListCreateView.as_view(), name="route-list"),
    path("routes/<int:pk>/", views.RouteDetailView.as_view(), name="route-detail"),
    path("routes/create_with_weather/", views.create_route_with_weather, name="create-route-with-weather"),
    path("routes/<int:route_id>/weather/", views.get_route_weather, name="route-weather"),
    path("travel_plans/", views.TravelPlanListCreateView.as_view(), name="travel-plan-list"),
    path("travel_plans/<int:pk>/", views.TravelPlanDetailView.as_view(), name="travel-plan-detail"),
    path("geocode/", views.geocode_location, name="geocode-location"),
]

