from typing import Any, cast

from openai import OpenAI

from app.config import settings

DOC_INTRO = "<document>\n"
DOC_OUTRO = "\n</document>\n"
CHUNK_TEMPLATE = """Here is the chunk we want to situate within the whole document:
<chunk>
{chunk}
</chunk>

Please give a short succinct context (50-100 tokens) to situate this chunk
within the overall document for the purposes of improving search retrieval
of the chunk. Answer only with the succinct context and nothing else."""


class ContextualEnricher:
    """Generates a contextual prefix per chunk via OpenRouter (Anthropic
    prompt-caching passthrough). The static document portion is wrapped in
    a `cache_control: ephemeral` block; the per-chunk tail is uncached.

    Cache TTL is ~5 minutes — batch chunks of one document back-to-back to
    maximise hits.

    Reference: https://www.anthropic.com/news/contextual-retrieval
    """

    def __init__(self) -> None:
        # Use a placeholder if no key — init must succeed without API key
        # so module imports cleanly in tests.
        api_key = settings.openrouter_api_key or "placeholder-no-key-set"
        self.client = OpenAI(
            base_url=settings.openrouter_base_url,
            api_key=api_key,
            default_headers={
                "HTTP-Referer": settings.openrouter_site_url,
                "X-Title": settings.openrouter_site_name,
            },
        )
        self.model = settings.cr_model

    def enrich(self, document: str, chunk: str) -> str:
        # cache_control is an Anthropic prompt-caching extension that
        # OpenRouter passes through; OpenAI's TypedDicts don't model it,
        # so we build the dict and cast it for the SDK call.
        messages: list[dict[str, Any]] = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": DOC_INTRO + document + DOC_OUTRO,
                        "cache_control": {"type": "ephemeral"},
                    },
                    {
                        "type": "text",
                        "text": CHUNK_TEMPLATE.format(chunk=chunk),
                    },
                ],
            }
        ]
        completion = self.client.chat.completions.create(
            model=self.model,
            max_tokens=200,
            messages=cast(Any, messages),
        )
        return (completion.choices[0].message.content or "").strip()

    def enrich_batch(self, document: str, chunks: list[str]) -> list[str]:
        """Same document, many chunks. First call warms the prefix cache."""
        return [self.enrich(document, c) for c in chunks]
