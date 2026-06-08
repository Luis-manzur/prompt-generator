from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import PromptJob
from .serializers import ImproveRequestSerializer, PromptJobSerializer
from .ollama_client import (
    OllamaClient,
    OllamaTimeoutError,
    OllamaUnavailableError,
    OllamaResponseError,
)
from .context import build_system_prompt
from .tokens import count_tokens


class ImproveView(APIView):
    def post(self, request):
        ser = ImproveRequestSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        prompt = ser.validated_data["prompt"]
        project_id = ser.validated_data.get("project_id")

        if project_id is not None:
            from apps.projects.models import Project
            get_object_or_404(Project, pk=project_id)

        raw_tokens = count_tokens(prompt)
        system_prompt = build_system_prompt(project_id)

        job = PromptJob.objects.create(
            project_id=project_id,
            raw_prompt=prompt,
            raw_tokens=raw_tokens,
            model_used=settings.OLLAMA_MODEL,
            status=PromptJob.STATUS_PENDING,
        )

        client = OllamaClient()
        try:
            improved = client.improve(system_prompt, prompt)
        except (OllamaTimeoutError, OllamaUnavailableError) as exc:
            job.status = PromptJob.STATUS_FAILED
            job.error = str(exc)
            job.save(update_fields=["status", "error"])
            return Response(
                {"error": "Ollama unavailable", "detail": str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except OllamaResponseError as exc:
            job.status = PromptJob.STATUS_FAILED
            job.error = str(exc)
            job.save(update_fields=["status", "error"])
            return Response(
                {"error": "Bad response from Ollama", "detail": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        improved_tokens = count_tokens(improved)
        job.improved_prompt = improved
        job.improved_tokens = improved_tokens
        job.token_delta = improved_tokens - raw_tokens
        job.status = PromptJob.STATUS_COMPLETED
        job.save(update_fields=["improved_prompt", "improved_tokens", "token_delta", "status"])

        return Response({
            "job_id": job.id,
            "improved_prompt": improved,
            "raw_tokens": raw_tokens,
            "improved_tokens": improved_tokens,
            "token_delta": job.token_delta,
            "model_used": job.model_used,
        })


class PromptJobDetailView(APIView):
    def get(self, request, job_id):
        job = get_object_or_404(PromptJob, pk=job_id)
        return Response(PromptJobSerializer(job).data)
