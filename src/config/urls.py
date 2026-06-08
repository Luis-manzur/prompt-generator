from django.urls import path, include

urlpatterns = [
    path('api/', include('apps.projects.urls')),
    path('api/', include('apps.improver.urls')),
]
