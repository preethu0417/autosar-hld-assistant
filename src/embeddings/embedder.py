# src/embeddings/embedder.py

from pathlib import Path
import json

from fastembed import TextEmbedding


class ArchitectureEmbedder:
    """
    Generates embeddings for AUTOSAR architecture chunks
    using a lightweight local embedding model.
    """

    def __init__(
        self,
        model_name="BAAI/bge-small-en-v1.5"
    ):
        self.model_name = model_name

        self.model = TextEmbedding(
            model_name=model_name
        )

    def embed_chunks(self, chunks):
        """
        Generate embeddings for chunk content.
        """

        texts = [
            chunk["content"]
            for chunk in chunks
        ]

        embeddings = list(
            self.model.embed(texts)
        )

        return embeddings

    def save_embeddings(
        self,
        output_path,
        chunks,
        embeddings
    ):
        """
        Save chunks and their embeddings together.
        """

        output_path = Path(
            output_path
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        records = []

        for chunk, embedding in zip(
            chunks,
            embeddings
        ):

            records.append({
                "content": chunk["content"],
                "metadata": chunk["metadata"],
                "embedding": embedding.tolist()
            })

        with open(
            output_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                records,
                file,
                indent=2,
                ensure_ascii=False
            )

        return output_path