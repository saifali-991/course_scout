"""CourseScout URL configuration — API lives under /api/ (see resources.urls)."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('resources.urls')),
]
