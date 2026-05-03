"""LLM generation: build a prompt from retrieved chunks and call an LLM."""
from __future__ import annotations

import logging
import os

from openai import OpenAI

logger = logging.getLogger(__name__)

_LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
_SYSTEM_PROMPT = (
    "You are a helpful assistant. Answer the user's question using ONLY the "
    "provided context. If the answer cannot be found in the context, say so clearly."
)


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

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    response = client.chat.completions.create(
        model=_LLM_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0,
    )
    answer = response.choices[0].message.content.strip()

    # Deduplicate source filenames while preserving order.
    seen: set[str] = set()
    sources: list[str] = []
    for chunk in chunks:
        fn = chunk["filename"]
        if fn not in seen:
            seen.add(fn)
            sources.append(fn)

    return answer, sources
