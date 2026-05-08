from langchain_text_splitters import RecursiveCharacterTextSplitter


def recursive_chunk(text: str, chunk_size: int = 800, overlap: int = 160) -> list[str]:
    if not text:
        return []
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return splitter.split_text(text)
