from rest_framework import serializers
from .models import Project, ProjectFile


class ProjectFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectFile
        fields = ['id', 'filename', 'content', 'version', 'created_at', 'updated_at']
        read_only_fields = ['version', 'created_at', 'updated_at']


class ProjectFileListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectFile
        fields = ['id', 'filename', 'version', 'updated_at']


class ProjectSerializer(serializers.ModelSerializer):
    files = ProjectFileListSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'files', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class ProjectListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
