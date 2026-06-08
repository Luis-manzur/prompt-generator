from django.db import models


class Project(models.Model):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class ProjectFile(models.Model):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='files'
    )
    filename = models.CharField(max_length=255)
    content = models.TextField()
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('project', 'filename')]
        ordering = ['filename']

    def __str__(self):
        return f"{self.project.name}/{self.filename} v{self.version}"
