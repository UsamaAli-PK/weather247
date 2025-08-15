from django.contrib import admin
from weather_data.admin import admin_site
from .models import Route, RouteWeatherPoint, RouteAlert, TravelPlan


@admin.register(Route, site=admin_site)
class RouteAdmin(admin.ModelAdmin):
	list_display = ('name', 'user', 'distance_km', 'estimated_duration_minutes', 'hazard_score', 'risk_level', 'created_at')
	list_filter = ('risk_level', 'created_at')
	search_fields = ('name', 'user__email', 'start_location', 'end_location')
	readonly_fields = ('created_at', 'updated_at')


@admin.register(RouteWeatherPoint, site=admin_site)
class RouteWeatherPointAdmin(admin.ModelAdmin):
	list_display = ('route', 'distance_from_start_km', 'temperature', 'wind_speed', 'visibility', 'hazard_score', 'timestamp')
	list_filter = ('timestamp',)
	search_fields = ('route__name',)
	readonly_fields = ('timestamp',)


@admin.register(RouteAlert, site=admin_site)
class RouteAlertAdmin(admin.ModelAdmin):
	list_display = ('route', 'alert_type', 'severity', 'distance_from_start_km', 'created_at')
	list_filter = ('alert_type', 'severity', 'created_at')
	search_fields = ('route__name', 'message')
	readonly_fields = ('created_at',)


@admin.register(TravelPlan, site=admin_site)
class TravelPlanAdmin(admin.ModelAdmin):
	list_display = ('route', 'user', 'planned_departure', 'planned_arrival', 'vehicle_type', 'created_at')
	list_filter = ('vehicle_type', 'planned_departure')
	search_fields = ('route__name', 'user__email')
	readonly_fields = ('created_at', 'updated_at')
