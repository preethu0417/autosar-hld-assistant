# src/chunking/architecture_chunker.py

from pathlib import Path
import json


class ArchitectureChunker:
    """
    Converts extracted AUTOSAR architecture knowledge
    into RAG-ready chunks while preserving
    complete architecture metadata.
    """

    def __init__(self, architecture_data):
        self.architecture_data = architecture_data

    def _create_chunk(
        self,
        content,
        entity_type,
        metadata
    ):
        """
        Create a chunk while preserving all
        architecture-specific metadata.
        """

        chunk_metadata = dict(metadata)

        chunk_metadata["entity_type"] = (
            entity_type
        )

        return {
            "content": content.strip(),
            "metadata": chunk_metadata
        }

    def create_chunks(self):
        """
        Create searchable chunks from all
        extracted architecture entities.
        """

        chunks = []

        self._chunk_components(chunks)
        self._chunk_ports(chunks)
        self._chunk_interfaces(chunks)
        self._chunk_data_flows(chunks)
        self._chunk_dependencies(chunks)
        self._chunk_functional_flows(chunks)
        self._chunk_relationships(chunks)

        return chunks

    def _chunk_components(self, chunks):

        for component in self.architecture_data.get(
            "components",
            []
        ):

            content = (
                f"Software Component: "
                f"{component['name']}. "
                f"This component is an AUTOSAR "
                f"software component."
            )

            chunks.append(
                self._create_chunk(
                    content,
                    "component",
                    component
                )
            )

    def _chunk_ports(self, chunks):

        for port in self.architecture_data.get(
            "ports",
            []
        ):

            content = (
                f"Port: {port['name']}."
            )

            chunks.append(
                self._create_chunk(
                    content,
                    "port",
                    port
                )
            )

    def _chunk_interfaces(self, chunks):

        for interface in self.architecture_data.get(
            "interfaces",
            []
        ):

            data_elements = ", ".join(
                interface.get(
                    "data_elements",
                    []
                )
            )

            content = (
                f"Interface: "
                f"{interface['name']}. "
                f"Provider: "
                f"{interface.get('provider')}. "
                f"Consumer: "
                f"{interface.get('consumer')}. "
                f"Data elements: "
                f"{data_elements}."
            )

            metadata = dict(interface)

            chunks.append(
                self._create_chunk(
                    content,
                    "interface",
                    metadata
                )
            )

    def _chunk_data_flows(self, chunks):

        for flow in self.architecture_data.get(
            "data_flows",
            []
        ):

            content = (
                f"Data flow: "
                f"{flow['signal']}. "
                f"Relationship: "
                f"{flow['relationship']}. "
                f"Component: "
                f"{flow['component']}."
            )

            chunks.append(
                self._create_chunk(
                    content,
                    "data_flow",
                    flow
                )
            )

    def _chunk_dependencies(self, chunks):

        for dependency in self.architecture_data.get(
            "dependencies",
            []
        ):

            content = (
                f"Dependency: "
                f"{dependency['dependent_component']} "
                f"depends on "
                f"{dependency['dependency_component']} "
                f"through "
                f"{dependency['data_element']}."
            )

            chunks.append(
                self._create_chunk(
                    content,
                    "dependency",
                    dependency
                )
            )

    def _chunk_functional_flows(self, chunks):

        for flow in self.architecture_data.get(
            "functional_flows",
            []
        ):

            description = (
                " ".join(
                    flow["description"].split()
                )
            )

            content = (
                f"Functional Flow Step "
                f"{flow['step']}: "
                f"{description}"
            )

            chunks.append(
                self._create_chunk(
                    content,
                    "functional_flow",
                    flow
                )
            )

    def _chunk_relationships(self, chunks):

        for relationship in self.architecture_data.get(
            "architecture_relationships",
            []
        ):

            content = (
                f"Architecture relationship: "
                f"{relationship['source_component']} "
                f"connects to "
                f"{relationship['target_component']} "
                f"through "
                f"{relationship['interface']}."
            )

            metadata = dict(
                relationship
            )

            chunks.append(
                self._create_chunk(
                    content,
                    "architecture_relationship",
                    metadata
                )
            )

    def save(
        self,
        output_path,
        chunks=None
    ):
        """
        Save generated chunks to JSON.
        """

        if chunks is None:
            chunks = self.create_chunks()

        output_path = Path(
            output_path
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            output_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                chunks,
                file,
                indent=2,
                ensure_ascii=False
            )

        return output_path