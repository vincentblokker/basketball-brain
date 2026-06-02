from app.retrieval.hybrid import rrf_fusion


def test_rrf_combines_two_rankings():
    vector_ids = ["a", "b", "c", "d", "e"]
    keyword_ids = ["c", "b", "f", "g", "a"]
    fused = rrf_fusion([vector_ids, keyword_ids], k=60)
    # b ranks high in both -> top
    # a ranks high in vector and last in keyword -> middle
    # c ranks middle in vector but top in keyword -> high
    assert fused[0] in ("b", "c")  # top is one of the cross-list winners
    assert "f" in fused
    assert fused.index("f") > fused.index("c")


def test_rrf_single_list_preserves_order():
    fused = rrf_fusion([["a", "b", "c"]], k=60)
    assert fused == ["a", "b", "c"]


def test_rrf_with_weights():
    # When keyword search is weighted 0, only vector ordering should matter
    vector_ids = ["x", "y", "z"]
    keyword_ids = ["z", "y", "x"]
    fused = rrf_fusion([vector_ids, keyword_ids], weights=[1.0, 0.0], k=60)
    assert fused == ["x", "y", "z"]


def test_rrf_handles_empty_lists():
    assert rrf_fusion([[], []]) == []
    assert rrf_fusion([["a"], []]) == ["a"]
