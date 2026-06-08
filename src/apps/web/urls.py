from django.urls import path
from . import views

urlpatterns = [
    path('', views.improve_page, name='web-improve-page'),
    path('improve/', views.improve, name='web-improve'),
    path('projects/', views.projects_page, name='web-projects'),
    path('projects/<int:project_pk>/delete/', views.project_delete,
         name='web-project-delete'),
    path('projects/<int:project_pk>/', views.project_detail,
         name='web-project-detail'),
    path('projects/<int:project_pk>/files/', views.file_upload,
         name='web-file-upload'),
    path('projects/<int:project_pk>/files/<int:file_pk>/delete/',
         views.file_delete, name='web-file-delete'),
]
