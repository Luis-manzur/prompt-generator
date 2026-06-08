from django.db import models


class PromptJob(models.Model):
    STATUS_PENDING = "pending"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED, "Failed"),
    ]

    project = models.ForeignKey(
        "projects.Project",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="prompt_jobs",
    )
    raw_prompt = models.TextField()
    improved_prompt = models.TextField(blank=True)
    raw_tokens = models.PositiveIntegerField()
    improved_tokens = models.PositiveIntegerField(default=0)
    token_delta = models.IntegerField(default=0)
    model_used = models.CharField(max_length=120)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["project"], name="improver_job_project_idx"),
            models.Index(fields=["created_at"], name="improver_job_created_idx"),
            models.Index(fields=["status"], name="improver_job_status_idx"),
        ]
