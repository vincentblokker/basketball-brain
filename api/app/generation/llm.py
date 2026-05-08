from openai import OpenAI

from app.config import settings
from app.generation.prompt import SYSTEM_PROMPT, build_user_prompt
from app.schemas import Chunk


class LLMGenerator:
    """LLM wrapper using OpenRouter (OpenAI-compatible API).
    Switch models by setting LLM_MODEL env var or settings.llm_model.
    """

    def __init__(self) -> None:
        # Use a placeholder when no key is configured so the SDK init succeeds.
        # Actual API calls will fail until a real key is supplied via env.
        api_key = settings.openrouter_api_key or "placeholder-no-key-configured"
        self.client = OpenAI(
            base_url=settings.openrouter_base_url,
            api_key=api_key,
            default_headers={
                "HTTP-Referer": settings.openrouter_site_url,
                "X-Title": settings.openrouter_site_name,
            },
        )
        self.model = settings.llm_model

    def answer(self, question: str, chunks: list[Chunk]) -> str:
        completion = self.client.chat.completions.create(
            model=self.model,
            max_tokens=1024,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(question, chunks)},
            ],
        )
        return completion.choices[0].message.content or ""
