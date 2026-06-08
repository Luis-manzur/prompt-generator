from django.urls import path
from .views import ImproveView, PromptJobDetailView

urlpatterns = [
    path("improve/", ImproveView.as_view(), name="improve"),
    path("improve/<int:job_id>/", PromptJobDetailView.as_view(), name="improve-detail"),
]
