from unittest.mock import MagicMock, patch

from app.ingest.contextual import ContextualEnricher


@patch("app.ingest.contextual.OpenAI")
def test_enrich_calls_openrouter_with_cache_control(mock_openai_cls):
    """The enricher must wrap the document in a cache_control: ephemeral block
    so OpenRouter caches the prefix on the Anthropic side."""
    mock_client = MagicMock()
    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock(message=MagicMock(content="contextual prefix here"))]
    mock_client.chat.completions.create.return_value = mock_completion
    mock_openai_cls.return_value = mock_client

    enricher = ContextualEnricher()
    result = enricher.enrich(
        document="full document body",
        chunk="specific chunk text",
    )

    assert result == "contextual prefix here"

    # Verify the call structure matches Anthropic prompt-caching contract
    call_args = mock_client.chat.completions.create.call_args
    kwargs = call_args.kwargs
    assert kwargs["model"].startswith("anthropic/")
    messages = kwargs["messages"]
    assert len(messages) == 1
    content_blocks = messages[0]["content"]
    assert len(content_blocks) == 2
    # Block 0: document, cached
    assert "full document body" in content_blocks[0]["text"]
    assert content_blocks[0]["cache_control"] == {"type": "ephemeral"}
    # Block 1: chunk-specific tail, no cache_control
    assert "specific chunk text" in content_blocks[1]["text"]
    assert "cache_control" not in content_blocks[1]


@patch("app.ingest.contextual.OpenAI")
def test_enrich_batch_calls_per_chunk(mock_openai_cls):
    """enrich_batch should call once per chunk so cache hits accumulate."""
    mock_client = MagicMock()
    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock(message=MagicMock(content="ctx"))]
    mock_client.chat.completions.create.return_value = mock_completion
    mock_openai_cls.return_value = mock_client

    enricher = ContextualEnricher()
    results = enricher.enrich_batch("doc body", ["chunk1", "chunk2", "chunk3"])

    assert results == ["ctx", "ctx", "ctx"]
    assert mock_client.chat.completions.create.call_count == 3


@patch("app.ingest.contextual.OpenAI")
def test_enrich_strips_whitespace_from_response(mock_openai_cls):
    mock_client = MagicMock()
    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock(message=MagicMock(content="  prefix with whitespace  \n"))]
    mock_client.chat.completions.create.return_value = mock_completion
    mock_openai_cls.return_value = mock_client

    enricher = ContextualEnricher()
    result = enricher.enrich("doc", "chunk")
    assert result == "prefix with whitespace"
