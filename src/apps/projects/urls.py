from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, ProjectFileView

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')

urlpatterns = [
    path('', include(router.urls)),
    path(
        'projects/<int:project_pk>/files/',
        ProjectFileView.as_view(),
        name='project-files-list',
    ),
    path(
        'projects/<int:project_pk>/files/<int:file_pk>/',
        ProjectFileView.as_view(),
        name='project-files-detail',
    ),
]
