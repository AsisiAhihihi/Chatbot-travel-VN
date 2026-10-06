"""LangChain adapter for local multilingual E5 embeddings."""


from langchain_huggingface import HuggingFaceEmbeddings


class SentenceTransformerEmbedder(HuggingFaceEmbeddings):
    def __init__(self, model_name: str = "intfloat/multilingual-e5-small") -> None:
        super().__init__(
            model_name=model_name,
            encode_kwargs={"normalize_embeddings": True},
        )

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return super().embed_documents([f"passage: {text}" for text in texts])

    def embed_query(self, text: str) -> list[float]:
        return super().embed_query(f"query: {text}")