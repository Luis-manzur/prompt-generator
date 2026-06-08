from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Project, ProjectFile
from .serializers import (
    ProjectSerializer,
    ProjectListSerializer,
    ProjectFileSerializer,
)


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.prefetch_related('files').all()
    http_method_names = ['get', 'post', 'delete', 'head', 'options']

    def get_serializer_class(self):
        if self.action == 'list':
            return ProjectListSerializer
        return ProjectSerializer


class ProjectFileView(APIView):

    def _get_project(self, project_pk):
        return get_object_or_404(Project, pk=project_pk)

    def get(self, request, project_pk, file_pk=None):
        project = self._get_project(project_pk)
        if file_pk is not None:
            pf = get_object_or_404(ProjectFile, pk=file_pk, project=project)
            return Response(ProjectFileSerializer(pf).data)
        return Response(ProjectFileSerializer(project.files.all(), many=True).data)

    def post(self, request, project_pk, file_pk=None):
        project = self._get_project(project_pk)
        if 'file' in request.FILES:
            uploaded = request.FILES['file']
            filename = uploaded.name
            content = uploaded.read().decode('utf-8')
        else:
            filename = request.data.get('filename')
            content = request.data.get('content')

        if not filename or content is None:
            return Response(
                {'error': 'filename and content are required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        existing = ProjectFile.objects.filter(project=project, filename=filename).first()
        if existing:
            existing.content = content
            existing.version += 1
            existing.save(update_fields=['content', 'version', 'updated_at'])
            return Response(ProjectFileSerializer(existing).data, status=status.HTTP_200_OK)

        pf = ProjectFile.objects.create(project=project, filename=filename, content=content)
        return Response(ProjectFileSerializer(pf).data, status=status.HTTP_201_CREATED)

    def delete(self, request, project_pk, file_pk):
        project = self._get_project(project_pk)
        pf = get_object_or_404(ProjectFile, pk=file_pk, project=project)
        pf.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
