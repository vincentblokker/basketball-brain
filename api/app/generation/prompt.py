from app.schemas import Chunk

SYSTEM_PROMPT = """Je bent Basketball Brain, een Nederlandse AI-assistent voor \
basketbalcoaches, scheidsrechters, ouders en spelers. Je antwoorden zijn:
- Volledig gegrond in de meegeleverde context. Verzin niets.
- Beknopt, direct, in het Nederlands tenzij de bron Engels is.
- Voorzien van expliciete verwijzingen naar de bron-titel en sectie/pagina.
- "Ik weet het niet op basis van de beschikbare bronnen" als de context geen antwoord bevat.

Antwoord-format:
[antwoord in 2-6 zinnen]

Bronnen: [titel — sectie/pagina, ...]"""

USER_TEMPLATE = """Vraag: {question}

Context:
{context}

Antwoord:"""


def build_user_prompt(question: str, chunks: list[Chunk]) -> str:
    blocks = []
    for c in chunks:
        loc = c.section or (f"p.{c.page}" if c.page else "")
        blocks.append(f"[{c.title} — {loc}]\n{c.text}")
    context = "\n\n---\n\n".join(blocks)
    return USER_TEMPLATE.format(question=question, context=context)
