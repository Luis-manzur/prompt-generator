import logging
from django.conf import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_BASE = (
    "You are a prompt-engineering expert. Rewrite the user's prompt to be "
    "token-economical (no filler), unambiguous (explicit task, constraints, "
    "output format), and structured only where structure helps. Preserve the "
    "user's original intent exactly. Output ONLY the improved prompt text — "
    "no preamble, no explanation, no markdown wrapper."
)


def assemble_context(project_id):
    if project_id is None:
        return ""

    from apps.projects.models import ProjectFile

    files = list(
        ProjectFile.objects.filter(project_id=project_id).order_by("filename")
    )
    if not files:
        return ""

    limit = getattr(settings, "OLLAMA_CONTEXT_LIMIT_CHARS", 8000)
    sorted_by_recency = sorted(files, key=lambda f: f.updated_at, reverse=True)

    included = []
    total = 0
    for f in sorted_by_recency:
        chunk = f"## {f.filename}\n\n{f.content}\n\n"
        if total + len(chunk) <= limit:
            included.append(f)
            total += len(chunk)
        else:
            logger.warning(
                "project %s context exceeds %d char limit; dropping file %s",
                project_id,
                limit,
                f.filename,
            )

    included.sort(key=lambda f: f.filename)
    return "".join(f"## {f.filename}\n\n{f.content}\n\n" for f in included)


def build_system_prompt(project_id):
    context = assemble_context(project_id)
    if not context:
        return SYSTEM_PROMPT_BASE
    return (
        SYSTEM_PROMPT_BASE
        + "\n\nThe following project context applies:\n\n"
        + context
        + "\nUse this context to inform the rewrite but do not reproduce it verbatim."
    )
