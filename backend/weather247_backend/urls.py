"""
URL configuration for weather247_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from weather_data.admin import admin_site

urlpatterns = [
    path('admin/', admin_site.urls),  # Use custom admin site
    path('django-admin/', admin.site.urls),  # Keep default admin as backup
    path('api/auth/', include('accounts.urls')),
    path('api/weather/', include('weather_data.urls')),
    path('api/routes/', include('route_planner.urls')),
]
