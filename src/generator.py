"""LLM generation: build a prompt from retrieved chunks and call an LLM."""
from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)

_LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")
_GAPGPT_API_URL = os.getenv(
    "GAPGPT_API_URL", "https://api.gapgpt.app/v1/chat/completions"
)
_GAPGPT_TIMEOUT_SECONDS = float(os.getenv("GAPGPT_TIMEOUT_SECONDS", "60"))
_SYSTEM_PROMPT = (
    "You are a helpful assistant. Answer the user's question using ONLY the "
    "provided context. If the answer cannot be found in the context, say so clearly."
)


def _gapgpt_chat(messages: list[dict[str, str]]) -> str:
    api_key = os.environ["GAPGPT_API_KEY"]
    payload = json.dumps(
        {
            "model": _LLM_MODEL,
            "messages": messages,
            "temperature": 0,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        _GAPGPT_API_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request, timeout=_GAPGPT_TIMEOUT_SECONDS
        ) as response:
            response_body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"GapGPT request failed with status {exc.code}: {error_body}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"GapGPT request failed: {exc.reason}") from exc

    data = json.loads(response_body)
    if "choices" in data:
        return data["choices"][0]["message"]["content"].strip()
    if "answer" in data:
        return str(data["answer"]).strip()
    if "text" in data:
        return str(data["text"]).strip()
    if "content" in data:
        return str(data["content"]).strip()

    raise RuntimeError("GapGPT response did not include an answer.")


def generate(question: str, chunks: list[dict]) -> tuple[str, list[str]]:
    """Call the LLM with *question* and the retrieved *chunks*.

    Args:
        question: The user's question.
        chunks:   List of chunk dicts (from the retriever) each with at least
                  ``text`` and ``filename`` keys.

    Returns:
        A tuple of ``(answer_text, source_filenames)`` where *source_filenames*
        is a deduplicated, ordered list of the PDFs that contributed context.
    """
    if not chunks:
        return (
            "I could not find any relevant context to answer your question.",
            [],
        )

    context_parts = []
    for i, chunk in enumerate(chunks, start=1):
        context_parts.append(f"[{i}] (source: {chunk['filename']})\n{chunk['text']}")
    context = "\n\n".join(context_parts)

    user_message = f"Context:\n{context}\n\nQuestion: {question}"

    answer = _gapgpt_chat(
        [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ]
    )

    # Deduplicate source filenames while preserving order.
    seen: set[str] = set()
    sources: list[str] = []
    for chunk in chunks:
        fn = chunk["filename"]
        if fn not in seen:
            seen.add(fn)
            sources.append(fn)

    return answer, sources
