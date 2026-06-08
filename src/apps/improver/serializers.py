from rest_framework import serializers
from .models import PromptJob


class ImproveRequestSerializer(serializers.Serializer):
    prompt = serializers.CharField(allow_blank=False, trim_whitespace=False)
    project_id = serializers.IntegerField(required=False, allow_null=True, default=None)

    def validate_prompt(self, value):
        if not value.strip():
            raise serializers.ValidationError("prompt must not be blank or whitespace-only")
        return value


class PromptJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromptJob
        fields = [
            "id",
            "project_id",
            "raw_prompt",
            "improved_prompt",
            "raw_tokens",
            "improved_tokens",
            "token_delta",
            "model_used",
            "status",
            "error",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "project_id",
            "raw_prompt",
            "improved_prompt",
            "raw_tokens",
            "improved_tokens",
            "token_delta",
            "model_used",
            "status",
            "error",
            "created_at",
        ]
