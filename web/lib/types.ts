export type Citation = {
  source_id: string;
  title: string;
  url: string;
  section: string | null;
  page: number | null;
  chunk_id: string;
};

export type Chunk = {
  chunk_id: string;
  source_id: string;
  title: string;
  text: string;
  url: string;
  section: string | null;
  page: number | null;
  contextual_prefix: string | null;
};

export type QueryResponse = {
  answer: string;
  citations: Citation[];
  retrieved_chunks: Chunk[];
};
