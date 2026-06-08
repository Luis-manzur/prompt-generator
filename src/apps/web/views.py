from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render

from apps.projects.models import Project, ProjectFile
from apps.improver.models import PromptJob
from apps.improver.context import build_system_prompt
from apps.improver.tokens import count_tokens
from apps.improver.ollama_client import (
    OllamaClient,
    OllamaTimeoutError,
    OllamaUnavailableError,
    OllamaResponseError,
)


def improve_page(request):
    return render(request, 'web/improve.html', {'projects': Project.objects.all()})


def improve(request):
    prompt = (request.POST.get('prompt') or '').strip()
    project_id = request.POST.get('project_id') or None

    if not prompt:
        return render(request, 'web/_result.html', {'error': 'Prompt is required.'})

    if project_id is not None:
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
        job.save(update_fields=['status', 'error'])
        return render(request, 'web/_result.html',
                      {'error': f'Ollama unavailable: {exc}'})
    except OllamaResponseError as exc:
        job.status = PromptJob.STATUS_FAILED
        job.error = str(exc)
        job.save(update_fields=['status', 'error'])
        return render(request, 'web/_result.html',
                      {'error': f'Bad response from Ollama: {exc}'})

    improved_tokens = count_tokens(improved)
    job.improved_prompt = improved
    job.improved_tokens = improved_tokens
    job.token_delta = improved_tokens - raw_tokens
    job.status = PromptJob.STATUS_COMPLETED
    job.save(update_fields=['improved_prompt', 'improved_tokens',
                            'token_delta', 'status'])

    return render(request, 'web/_result.html', {'job': job})


def projects_page(request):
    if request.method == 'POST':
        name = (request.POST.get('name') or '').strip()
        description = (request.POST.get('description') or '').strip()
        if name and not Project.objects.filter(name=name).exists():
            Project.objects.create(name=name, description=description)
        return render(request, 'web/_project_list.html',
                      {'projects': Project.objects.all()})
    return render(request, 'web/projects.html',
                  {'projects': Project.objects.all()})


def project_delete(request, project_pk):
    Project.objects.filter(pk=project_pk).delete()
    return render(request, 'web/_project_list.html',
                  {'projects': Project.objects.all()})


def project_detail(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk)
    return render(request, 'web/project_detail.html', {'project': project})


def file_upload(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk)

    if 'file' in request.FILES:
        uploaded = request.FILES['file']
        filename = uploaded.name
        content = uploaded.read().decode('utf-8')
    else:
        filename = (request.POST.get('filename') or '').strip()
        content = request.POST.get('content')

    if filename and content is not None:
        existing = ProjectFile.objects.filter(
            project=project, filename=filename).first()
        if existing:
            existing.content = content
            existing.version += 1
            existing.save(update_fields=['content', 'version', 'updated_at'])
        else:
            ProjectFile.objects.create(
                project=project, filename=filename, content=content)

    return render(request, 'web/_file_list.html', {'project': project})


def file_delete(request, project_pk, file_pk):
    project = get_object_or_404(Project, pk=project_pk)
    ProjectFile.objects.filter(pk=file_pk, project=project).delete()
    return render(request, 'web/_file_list.html', {'project': project})
