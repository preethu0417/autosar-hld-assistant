# src/retrieval/retriever.py

from pathlib import Path
import json
import re

import faiss
import numpy as np

from src.embeddings.embedder import ArchitectureEmbedder


class ArchitectureRetriever:
    """
    Hybrid retrieval over AUTOSAR architecture knowledge.

    Supports:
    1. Semantic retrieval using FastEmbed + FAISS
    2. Structured architecture-aware retrieval
    3. Hybrid retrieval
    4. Both legacy and production RAG document formats
    """

    def __init__(
        self,
        model_name="BAAI/bge-small-en-v1.5"
    ):

        self.embedder = ArchitectureEmbedder(
            model_name=model_name
        )

        self.chunks = []
        self.index = None

    # =========================================================
    # NORMALIZE DOCUMENT FORMAT
    # =========================================================

    def _normalize_chunk(self, chunk):
        """
        Convert both legacy RAG records and production
        chunk records into one standard format.

        Production format:

        {
            "content": "...",
            "metadata": {...}
        }

        Legacy format:

        {
            "type": "...",
            "name": "...",
            "text": "...",
            "document": "...",
            "page": ...,
            ...
        }
        """

        # -----------------------------------------------------
        # Already in production format
        # -----------------------------------------------------

        if (
            isinstance(chunk, dict)
            and "content" in chunk
            and "metadata" in chunk
        ):

            metadata = dict(
                chunk.get("metadata", {})
            )

            if "entity_type" not in metadata:

                entity_type = metadata.get(
                    "type",
                    ""
                )

                if entity_type:

                    metadata["entity_type"] = (
                        str(entity_type)
                        .lower()
                    )

            return {
                "content": str(
                    chunk.get(
                        "content",
                        ""
                    )
                ),
                "metadata": metadata
            }

        # -----------------------------------------------------
        # Legacy format
        # -----------------------------------------------------

        if not isinstance(
            chunk,
            dict
        ):

            raise ValueError(
                "Invalid RAG document record."
            )

        # Content may be stored as text
        content = chunk.get(
            "text"
        )

        if content is None:

            content = chunk.get(
                "content"
            )

        if content is None:

            content = chunk.get(
                "description",
                ""
            )

        # -----------------------------------------------------
        # Metadata
        # -----------------------------------------------------

        metadata = {}

        # If metadata already exists
        if isinstance(
            chunk.get("metadata"),
            dict
        ):

            metadata.update(
                chunk["metadata"]
            )

        # Copy legacy top-level fields
        ignored_fields = {
            "text",
            "content",
            "metadata"
        }

        for key, value in chunk.items():

            if key not in ignored_fields:

                metadata[key] = value

        # -----------------------------------------------------
        # Entity type
        # -----------------------------------------------------

        entity_type = metadata.get(
            "entity_type"
        )

        if not entity_type:

            entity_type = metadata.get(
                "type",
                ""
            )

        entity_type = str(
            entity_type
        ).strip()

        # Normalize type names
        type_mapping = {
            "interface": "interface",
            "data_flow": "data_flow",
            "data flow": "data_flow",
            "dependency": "dependency",
            "functional_flow": "functional_flow",
            "functional flow": "functional_flow",
            "component": "component",
            "port": "port",
            "architecture_relationship":
                "architecture_relationship",
            "architecture relationship":
                "architecture_relationship"
        }

        normalized_type = type_mapping.get(
            entity_type.lower(),
            entity_type.lower()
        )

        metadata["entity_type"] = (
            normalized_type
        )

        # -----------------------------------------------------
        # Legacy records often use "name"
        # -----------------------------------------------------

        if (
            normalized_type == "data_flow"
            and not metadata.get("signal")
        ):

            if metadata.get("name"):

                metadata["signal"] = (
                    metadata["name"]
                )

        # -----------------------------------------------------
        # Return standard production structure
        # -----------------------------------------------------

        return {
            "content": str(
                content
            ).strip(),
            "metadata": metadata
        }

    # =========================================================
    # NORMALIZE ALL CHUNKS
    # =========================================================

    def _normalize_chunks(self, chunks):

        normalized = []

        for chunk in chunks:

            normalized.append(
                self._normalize_chunk(
                    chunk
                )
            )

        return normalized

    # =========================================================
    # BUILD INDEX
    # =========================================================

    def build_index(self, chunks):
        """
        Generate embeddings and build a FAISS
        cosine-similarity index.
        """

        self.chunks = (
            self._normalize_chunks(
                chunks
            )
        )

        if not self.chunks:

            raise ValueError(
                "No chunks were provided."
            )

        embeddings = (
            self.embedder.embed_chunks(
                self.chunks
            )
        )

        matrix = np.asarray(
            embeddings,
            dtype="float32"
        )

        faiss.normalize_L2(
            matrix
        )

        dimension = matrix.shape[1]

        self.index = faiss.IndexFlatIP(
            dimension
        )

        self.index.add(
            matrix
        )

        return self.index

    # =========================================================
    # SEMANTIC SEARCH
    # =========================================================

    def search(
        self,
        query,
        top_k=5
    ):
        """
        Semantic search using FAISS.
        """

        if self.index is None:

            raise RuntimeError(
                "FAISS index has not been built."
            )

        query_embedding = (
            self.embedder.embed_chunks(
                [
                    {
                        "content": query,
                        "metadata": {}
                    }
                ]
            )[0]
        )

        query_vector = np.asarray(
            [query_embedding],
            dtype="float32"
        )

        faiss.normalize_L2(
            query_vector
        )

        actual_top_k = min(
            top_k,
            self.index.ntotal
        )

        scores, indices = (
            self.index.search(
                query_vector,
                actual_top_k
            )
        )

        results = []

        for score, index in zip(
            scores[0],
            indices[0]
        ):

            if index < 0:
                continue

            chunk = self.chunks[
                int(index)
            ]

            results.append({
                "content": chunk.get(
                    "content",
                    ""
                ),
                "metadata": chunk.get(
                    "metadata",
                    {}
                ),
                "score": float(score),
                "retrieval_type": "semantic"
            })

        return results

    # =========================================================
    # QUERY INTENT
    # =========================================================

    def _detect_intent(self, query):

        query_lower = query.lower()

        if (
            "what interface"
            in query_lower
            or "which interface"
            in query_lower
        ):

            return "interface"

        if (
            "connect" in query_lower
            and (
                "interface"
                in query_lower
                or "between"
                in query_lower
            )
        ):

            return "interface"

        if (
            "which component consumes"
            in query_lower
            or "what component consumes"
            in query_lower
        ):

            return "consume"

        if (
            "which component provides"
            in query_lower
            or "what component provides"
            in query_lower
        ):

            return "provide"

        if (
            "which components depend"
            in query_lower
            or "what components depend"
            in query_lower
        ):

            return "dependency"

        if (
            "functional flow"
            in query_lower
        ):

            return "functional_flow"

        return "general"

    # =========================================================
    # QUERY ENTITY EXTRACTION
    # =========================================================

    def _query_entities(self, query):

        query_lower = query.lower()

        entities = set()

        possible_fields = [
            "name",
            "component",
            "provider",
            "consumer",
            "dependent_component",
            "dependency_component",
            "source_component",
            "target_component",
            "signal",
            "interface",
            "data_element"
        ]

        for chunk in self.chunks:

            metadata = chunk.get(
                "metadata",
                {}
            )

            for field in possible_fields:

                value = metadata.get(
                    field
                )

                if not value:
                    continue

                if isinstance(
                    value,
                    list
                ):

                    values = value

                else:

                    values = [value]

                for item in values:

                    item_text = str(
                        item
                    )

                    item_lower = (
                        item_text.lower()
                    )

                    if (
                        item_lower
                        and item_lower
                        in query_lower
                    ):

                        entities.add(
                            item_lower
                        )

        return list(
            entities
        )

    # =========================================================
    # STRUCTURED SEARCH
    # =========================================================

    def structured_search(
        self,
        query
    ):
        """
        Architecture-aware structured retrieval.
        """

        intent = (
            self._detect_intent(
                query
            )
        )

        query_entities = (
            self._query_entities(
                query
            )
        )

        results = []

        for chunk in self.chunks:

            metadata = chunk.get(
                "metadata",
                {}
            )

            entity_type = str(
                metadata.get(
                    "entity_type",
                    ""
                )
            ).lower()

            score = 0.0

            # =================================================
            # INTERFACE
            # =================================================

            if intent == "interface":

                if (
                    entity_type
                    == "interface"
                ):

                    provider = str(
                        metadata.get(
                            "provider",
                            ""
                        )
                    ).lower()

                    consumer = str(
                        metadata.get(
                            "consumer",
                            ""
                        )
                    ).lower()

                    provider_match = (
                        provider
                        in query_entities
                    )

                    consumer_match = (
                        consumer
                        in query_entities
                    )

                    if (
                        provider_match
                        and consumer_match
                    ):

                        score = 100.0

                    elif (
                        provider_match
                        or consumer_match
                    ):

                        score = 20.0

                elif (
                    entity_type
                    == "architecture_relationship"
                ):

                    source = str(
                        metadata.get(
                            "source_component",
                            ""
                        )
                    ).lower()

                    target = str(
                        metadata.get(
                            "target_component",
                            ""
                        )
                    ).lower()

                    source_match = (
                        source
                        in query_entities
                    )

                    target_match = (
                        target
                        in query_entities
                    )

                    if (
                        source_match
                        and target_match
                    ):

                        score = 90.0

                    elif (
                        source_match
                        or target_match
                    ):

                        score = 15.0

            # =================================================
            # CONSUMER
            # =================================================

            elif intent == "consume":

                if (
                    entity_type
                    == "data_flow"
                ):

                    signal = str(
                        metadata.get(
                            "signal",
                            ""
                        )
                    ).lower()

                    component = str(
                        metadata.get(
                            "component",
                            ""
                        )
                    ).lower()

                    relationship = str(
                        metadata.get(
                            "relationship",
                            ""
                        )
                    ).lower()

                    signal_match = (
                        signal
                        in query_entities
                    )

                    component_match = (
                        component
                        in query_entities
                    )

                    if (
                        signal_match
                        and component_match
                        and relationship
                        == "consumed"
                    ):

                        score = 100.0

                    elif (
                        signal_match
                        and relationship
                        == "consumed"
                    ):

                        score = 80.0

                    elif (
                        signal_match
                        and relationship
                        in (
                            "produced",
                            "generated"
                        )
                    ):

                        score = 20.0

            # =================================================
            # PROVIDER
            # =================================================

            elif intent == "provide":

                if (
                    entity_type
                    == "interface"
                ):

                    provider = str(
                        metadata.get(
                            "provider",
                            ""
                        )
                    ).lower()

                    if (
                        provider
                        in query_entities
                    ):

                        score = 100.0

                elif (
                    entity_type
                    == "data_flow"
                ):

                    component = str(
                        metadata.get(
                            "component",
                            ""
                        )
                    ).lower()

                    relationship = str(
                        metadata.get(
                            "relationship",
                            ""
                        )
                    ).lower()

                    if (
                        component
                        in query_entities
                        and relationship
                        in (
                            "produced",
                            "generated"
                        )
                    ):

                        score = 90.0

            # =================================================
            # DEPENDENCY
            # =================================================

            elif intent == "dependency":

                if (
                    entity_type
                    == "dependency"
                ):

                    dependent = str(
                        metadata.get(
                            "dependent_component",
                            ""
                        )
                    ).lower()

                    dependency = str(
                        metadata.get(
                            "dependency_component",
                            ""
                        )
                    ).lower()

                    if (
                        dependency
                        in query_entities
                    ):

                        score = 100.0

                        if (
                            dependent
                            in query_entities
                        ):

                            score = 110.0

            # =================================================
            # FUNCTIONAL FLOW
            # =================================================

            elif (
                intent
                == "functional_flow"
            ):

                if (
                    entity_type
                    == "functional_flow"
                ):

                    description = str(
                        metadata.get(
                            "description",
                            ""
                        )
                    ).lower()

                    matched_entities = sum(
                        entity in description
                        for entity
                        in query_entities
                    )

                    if (
                        matched_entities
                        > 0
                    ):

                        score = (
                            50.0
                            + (
                                matched_entities
                                * 10.0
                            )
                        )

            # =================================================
            # GENERAL SEARCH
            # =================================================

            else:

                content = str(
                    chunk.get(
                        "content",
                        ""
                    )
                ).lower()

                if query_entities:

                    matched_entities = sum(
                        entity in content
                        for entity
                        in query_entities
                    )

                    if matched_entities > 0:

                        score = (
                            matched_entities
                            / len(
                                query_entities
                            )
                        )

            # =================================================
            # ADD RESULT
            # =================================================

            if score > 0:

                results.append({
                    "content": chunk.get(
                        "content",
                        ""
                    ),
                    "metadata": metadata,
                    "score": float(score),
                    "retrieval_type":
                        "structured"
                })

        results.sort(
            key=lambda item: item["score"],
            reverse=True
        )

        return results

    # =========================================================
    # HYBRID SEARCH
    # =========================================================

    def hybrid_search(
        self,
        query,
        top_k=5
    ):
        """
        Combine semantic and structured retrieval.
        Structured results receive priority.
        """

        semantic_results = (
            self.search(
                query,
                top_k=top_k
            )
        )

        structured_results = (
            self.structured_search(
                query
            )
        )

        combined = (
            structured_results
            + semantic_results
        )

        unique_results = []

        seen = set()

        for result in combined:

            metadata = result.get(
                "metadata",
                {}
            )

            key = (
                result.get(
                    "content",
                    ""
                ),
                metadata.get(
                    "document"
                ),
                metadata.get(
                    "page"
                ),
                metadata.get(
                    "section_number"
                )
            )

            if key in seen:
                continue

            seen.add(key)

            unique_results.append(
                result
            )

        unique_results.sort(
            key=lambda item: item["score"],
            reverse=True
        )

        return unique_results[
            :top_k
        ]

    # =========================================================
    # SAVE INDEX
    # =========================================================

    def save_index(
        self,
        index_path,
        chunks_path
    ):
        """
        Save FAISS index and normalized chunks.
        """

        if self.index is None:

            raise RuntimeError(
                "Cannot save an empty FAISS index."
            )

        index_path = Path(
            index_path
        )

        chunks_path = Path(
            chunks_path
        )

        index_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        chunks_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        faiss.write_index(
            self.index,
            str(index_path)
        )

        with open(
            chunks_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                self.chunks,
                file,
                indent=2,
                ensure_ascii=False
            )

    # =========================================================
    # LOAD INDEX
    # =========================================================

    def load_index(
        self,
        index_path,
        chunks_path
    ):
        """
        Load an existing FAISS index and normalize
        either legacy or production RAG documents.
        """

        index_path = Path(
            index_path
        )

        chunks_path = Path(
            chunks_path
        )

        if not index_path.exists():

            raise FileNotFoundError(
                f"FAISS index not found: "
                f"{index_path}"
            )

        if not chunks_path.exists():

            raise FileNotFoundError(
                f"RAG documents not found: "
                f"{chunks_path}"
            )

        # -----------------------------------------------------
        # Load FAISS
        # -----------------------------------------------------

        self.index = faiss.read_index(
            str(index_path)
        )

        # -----------------------------------------------------
        # Load documents
        # -----------------------------------------------------

        with open(
            chunks_path,
            "r",
            encoding="utf-8"
        ) as file:

            raw_chunks = json.load(
                file
            )

        # -----------------------------------------------------
        # Normalize legacy / production format
        # -----------------------------------------------------

        self.chunks = (
            self._normalize_chunks(
                raw_chunks
            )
        )

        # -----------------------------------------------------
        # Safety check
        # -----------------------------------------------------

        if (
            self.index.ntotal
            != len(self.chunks)
        ):

            raise ValueError(
                "FAISS index and RAG document count "
                "do not match. "
                f"Index contains {self.index.ntotal} "
                f"vectors but "
                f"{len(self.chunks)} documents "
                f"were loaded."
            )

        return self