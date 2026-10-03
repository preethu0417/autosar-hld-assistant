# src/generation/answer_generator.py

from pathlib import Path
import json


class ArchitectureAnswerGenerator:
    """
    Generates evidence-grounded answers from retrieved
    AUTOSAR architecture evidence.

    The generator is deterministic and does not require
    an external LLM.

    It performs:
    1. Question intent detection
    2. Query entity detection
    3. Evidence filtering
    4. Architecture-specific answer generation
    5. Citation generation
    """

    def __init__(self):
        pass

    # =========================================================
    # QUESTION INTENT
    # =========================================================

    def _detect_intent(self, query):

        query_lower = query.lower()

        # -----------------------------------------------------
        # Interface questions
        # -----------------------------------------------------

        if (
            "what interface" in query_lower
            or "which interface" in query_lower
        ):
            return "interface"

        if (
            "connect" in query_lower
            and (
                "interface" in query_lower
                or "between" in query_lower
            )
        ):
            return "interface"

        # -----------------------------------------------------
        # Consumer questions
        # -----------------------------------------------------

        if (
            "which component consumes"
            in query_lower
            or "what component consumes"
            in query_lower
            or "which components consume"
            in query_lower
            or "what components consume"
            in query_lower
        ):
            return "consume"

        # -----------------------------------------------------
        # Provider questions
        # -----------------------------------------------------

        if (
            "which component provides"
            in query_lower
            or "what component provides"
            in query_lower
            or "which components provide"
            in query_lower
            or "what components provide"
            in query_lower
        ):
            return "provide"

        # -----------------------------------------------------
        # Dependency questions
        # -----------------------------------------------------

        if (
            "which components depend"
            in query_lower
            or "what components depend"
            in query_lower
            or "which component depends"
            in query_lower
            or "what component depends"
            in query_lower
        ):
            return "dependency"

        # -----------------------------------------------------
        # Functional flow questions
        # -----------------------------------------------------

        if "functional flow" in query_lower:
            return "functional_flow"

        if (
            "flow from" in query_lower
            or "flow between" in query_lower
        ):
            return "functional_flow"

        return "general"

    # =========================================================
    # QUERY ENTITIES
    # =========================================================

    def _find_query_entities(
        self,
        query,
        evidence
    ):
        """
        Find architecture entities mentioned in
        the question using retrieved metadata.
        """

        query_lower = query.lower()

        entities = []

        fields = [
            "name",
            "provider",
            "consumer",
            "component",
            "dependent_component",
            "dependency_component",
            "source_component",
            "target_component",
            "signal",
            "interface",
            "data_element"
        ]

        for result in evidence:

            metadata = result.get(
                "metadata",
                {}
            )

            for field in fields:

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

                    item = str(item)

                    if (
                        item.lower()
                        in query_lower
                    ):

                        if item not in entities:

                            entities.append(
                                item
                            )

        return entities

    # =========================================================
    # CITATION
    # =========================================================

    def _format_citation(
        self,
        metadata
    ):

        document = metadata.get(
            "document",
            "Unknown document"
        )

        page = metadata.get(
            "page",
            "Unknown"
        )

        section_number = metadata.get(
            "section_number",
            ""
        )

        section_title = metadata.get(
            "section_title",
            "Unknown section"
        )

        if section_number:

            section = (
                f"Section {section_number}: "
                f"{section_title}"
            )

        else:

            section = section_title

        return (
            f"{document} | "
            f"Page {page} | "
            f"{section}"
        )

    # =========================================================
    # DEDUPLICATION
    # =========================================================

    def _deduplicate_evidence(
        self,
        results
    ):

        unique = []

        seen = set()

        for result in results:

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

            unique.append(
                result
            )

        return unique

    # =========================================================
    # FILTER EVIDENCE BY INTENT
    # =========================================================

    def _filter_evidence_for_query(
        self,
        query,
        evidence,
        intent
    ):
        """
        Apply question-specific filtering after retrieval.

        This prevents semantically related but incorrect
        evidence from appearing in the final answer.
        """

        query_lower = query.lower()

        filtered = []

        # =====================================================
        # CONSUMER
        # =====================================================

        if intent == "consume":

            requested_signals = []

            for result in evidence:

                metadata = result.get(
                    "metadata",
                    {}
                )

                signal = metadata.get(
                    "signal"
                )

                if not signal:
                    continue

                signal_text = str(
                    signal
                )

                if (
                    signal_text.lower()
                    in query_lower
                ):

                    if signal_text not in requested_signals:

                        requested_signals.append(
                            signal_text
                        )

            for result in evidence:

                metadata = result.get(
                    "metadata",
                    {}
                )

                if metadata.get(
                    "entity_type"
                ) != "data_flow":

                    continue

                relationship = str(
                    metadata.get(
                        "relationship",
                        ""
                    )
                ).lower()

                if relationship != "consumed":
                    continue

                signal = str(
                    metadata.get(
                        "signal",
                        ""
                    )
                )

                if (
                    signal.lower()
                    in [
                        item.lower()
                        for item
                        in requested_signals
                    ]
                ):

                    filtered.append(
                        result
                    )

            return filtered

        # =====================================================
        # PROVIDER
        # =====================================================

        if intent == "provide":

            requested_signals = []

            for result in evidence:

                metadata = result.get(
                    "metadata",
                    {}
                )

                signal = metadata.get(
                    "signal"
                )

                if signal:

                    signal_text = str(
                        signal
                    )

                    if (
                        signal_text.lower()
                        in query_lower
                    ):

                        requested_signals.append(
                            signal_text
                        )

            for result in evidence:

                metadata = result.get(
                    "metadata",
                    {}
                )

                entity_type = metadata.get(
                    "entity_type"
                )

                # Data-flow provider
                if entity_type == "data_flow":

                    relationship = str(
                        metadata.get(
                            "relationship",
                            ""
                        )
                    ).lower()

                    signal = str(
                        metadata.get(
                            "signal",
                            ""
                        )
                    )

                    if relationship not in (
                        "produced",
                        "generated"
                    ):
                        continue

                    if requested_signals:

                        if (
                            signal.lower()
                            not in [
                                item.lower()
                                for item
                                in requested_signals
                            ]
                        ):
                            continue

                    filtered.append(
                        result
                    )

                # Interface provider
                elif entity_type == "interface":

                    provider = str(
                        metadata.get(
                            "provider",
                            ""
                        )
                    )

                    if (
                        provider.lower()
                        in query_lower
                    ):

                        filtered.append(
                            result
                        )

            return filtered

        # =====================================================
        # INTERFACE
        # =====================================================

        if intent == "interface":

            query_entities = []

            possible_fields = [
                "provider",
                "consumer",
                "source_component",
                "target_component"
            ]

            for result in evidence:

                metadata = result.get(
                    "metadata",
                    {}
                )

                for field in possible_fields:

                    value = metadata.get(
                        field
                    )

                    if not value:
                        continue

                    value = str(
                        value
                    )

                    if (
                        value.lower()
                        in query_lower
                    ):

                        if value not in query_entities:

                            query_entities.append(
                                value
                            )

            for result in evidence:

                metadata = result.get(
                    "metadata",
                    {}
                )

                entity_type = metadata.get(
                    "entity_type"
                )

                if entity_type == "interface":

                    provider = str(
                        metadata.get(
                            "provider",
                            ""
                        )
                    )

                    consumer = str(
                        metadata.get(
                            "consumer",
                            ""
                        )
                    )

                    provider_match = (
                        provider.lower()
                        in query_lower
                    )

                    consumer_match = (
                        consumer.lower()
                        in query_lower
                    )

                    if (
                        provider_match
                        and consumer_match
                    ):

                        filtered.append(
                            result
                        )

                elif (
                    entity_type
                    == "architecture_relationship"
                ):

                    source = str(
                        metadata.get(
                            "source_component",
                            ""
                        )
                    )

                    target = str(
                        metadata.get(
                            "target_component",
                            ""
                        )
                    )

                    if (
                        source.lower()
                        in query_lower
                        and target.lower()
                        in query_lower
                    ):

                        filtered.append(
                            result
                        )

            return filtered

        # =====================================================
        # DEPENDENCY
        # =====================================================

        if intent == "dependency":

            requested_component = None

            # Try to identify the component after
            # "depend on"

            dependency_match = (
                "depend on"
                in query_lower
            )

            for result in evidence:

                metadata = result.get(
                    "metadata",
                    {}
                )

                if metadata.get(
                    "entity_type"
                ) != "dependency":

                    continue

                dependency_component = str(
                    metadata.get(
                        "dependency_component",
                        ""
                    )
                )

                if (
                    dependency_component.lower()
                    in query_lower
                ):

                    requested_component = (
                        dependency_component
                    )

                    break

            for result in evidence:

                metadata = result.get(
                    "metadata",
                    {}
                )

                if metadata.get(
                    "entity_type"
                ) != "dependency":

                    continue

                dependency_component = str(
                    metadata.get(
                        "dependency_component",
                        ""
                    )
                )

                if requested_component:

                    if (
                        dependency_component.lower()
                        == requested_component.lower()
                    ):

                        filtered.append(
                            result
                        )

                elif dependency_match:

                    if (
                        dependency_component.lower()
                        in query_lower
                    ):

                        filtered.append(
                            result
                        )

            return filtered

        # =====================================================
        # FUNCTIONAL FLOW
        # =====================================================

        if intent == "functional_flow":

            for result in evidence:

                metadata = result.get(
                    "metadata",
                    {}
                )

                if metadata.get(
                    "entity_type"
                ) == "functional_flow":

                    filtered.append(
                        result
                    )

            # Sort by step
            filtered.sort(
                key=lambda item:
                item.get(
                    "metadata",
                    {}
                ).get(
                    "step",
                    999
                )
            )

            return filtered

        # =====================================================
        # GENERAL
        # =====================================================

        return evidence

    # =========================================================
    # INTERFACE ANSWER
    # =========================================================

    def _generate_interface_answer(
        self,
        query,
        evidence
    ):

        interfaces = []

        for result in evidence:

            metadata = result.get(
                "metadata",
                {}
            )

            if metadata.get(
                "entity_type"
            ) != "interface":

                continue

            provider = str(
                metadata.get(
                    "provider",
                    ""
                )
            )

            consumer = str(
                metadata.get(
                    "consumer",
                    ""
                )
            )

            interfaces.append({
                "name": metadata.get(
                    "name"
                ),
                "provider": provider,
                "consumer": consumer,
                "data_elements":
                    metadata.get(
                        "data_elements",
                        []
                    ),
                "citation":
                    self._format_citation(
                        metadata
                    )
            })

        if not interfaces:

            return (
                "I could not find a directly "
                "supported interface relationship "
                "in the retrieved architecture evidence."
            )

        lines = [
            "The interface relationship found "
            "in the HLD is:"
        ]

        seen = set()

        for interface in interfaces:

            key = (
                interface["name"],
                interface["provider"],
                interface["consumer"]
            )

            if key in seen:
                continue

            seen.add(key)

            lines.append(
                f"- {interface['name']} "
                f"connects "
                f"{interface['provider']} "
                f"to "
                f"{interface['consumer']}."
            )

            if interface[
                "data_elements"
            ]:

                elements = ", ".join(
                    interface[
                        "data_elements"
                    ]
                )

                lines.append(
                    f"  Data elements: "
                    f"{elements}."
                )

            lines.append(
                f"  Citation: "
                f"{interface['citation']}"
            )

        return "\n".join(
            lines
        )

    # =========================================================
    # CONSUMER ANSWER
    # =========================================================

    def _generate_consumer_answer(
        self,
        query,
        evidence
    ):
        """
        Generate a consumer answer only for
        the signal explicitly requested.
        """

        query_lower = query.lower()

        consumers = []

        for result in evidence:

            metadata = result.get(
                "metadata",
                {}
            )

            if metadata.get(
                "entity_type"
            ) != "data_flow":

                continue

            relationship = str(
                metadata.get(
                    "relationship",
                    ""
                )
            ).lower()

            if relationship != "consumed":
                continue

            signal = str(
                metadata.get(
                    "signal",
                    ""
                )
            )

            component = metadata.get(
                "component"
            )

            if not signal or not component:
                continue

            # Only answer for the signal
            # explicitly mentioned in the query.

            if signal.lower() not in query_lower:
                continue

            consumers.append({
                "component": component,
                "signal": signal,
                "citation":
                    self._format_citation(
                        metadata
                    )
            })

        if not consumers:

            return (
                "I could not find a directly "
                "supported consumer relationship "
                "for the requested data in the "
                "retrieved architecture evidence."
            )

        lines = [
            "The component consuming the "
            "requested data is:"
        ]

        seen = set()

        for item in consumers:

            key = (
                item["component"],
                item["signal"]
            )

            if key in seen:
                continue

            seen.add(key)

            lines.append(
                f"- {item['component']} "
                f"consumes "
                f"{item['signal']}."
            )

            lines.append(
                f"  Citation: "
                f"{item['citation']}"
            )

        return "\n".join(
            lines
        )

    # =========================================================
    # PROVIDER ANSWER
    # =========================================================

    def _generate_provider_answer(
        self,
        evidence
    ):

        providers = []

        for result in evidence:

            metadata = result.get(
                "metadata",
                {}
            )

            entity_type = metadata.get(
                "entity_type"
            )

            if entity_type == "interface":

                providers.append({
                    "provider":
                        metadata.get(
                            "provider"
                        ),
                    "interface":
                        metadata.get(
                            "name"
                        ),
                    "citation":
                        self._format_citation(
                            metadata
                        )
                })

            elif entity_type == "data_flow":

                relationship = str(
                    metadata.get(
                        "relationship",
                        ""
                    )
                ).lower()

                if relationship not in (
                    "produced",
                    "generated"
                ):
                    continue

                providers.append({
                    "provider":
                        metadata.get(
                            "component"
                        ),
                    "interface":
                        metadata.get(
                            "signal"
                        ),
                    "citation":
                        self._format_citation(
                            metadata
                        )
                })

        if not providers:

            return (
                "I could not find a directly "
                "supported provider relationship "
                "in the retrieved architecture evidence."
            )

        lines = [
            "The component providing the "
            "requested data is:"
        ]

        seen = set()

        for item in providers:

            key = (
                item["provider"],
                item["interface"]
            )

            if key in seen:
                continue

            seen.add(key)

            lines.append(
                f"- {item['provider']} "
                f"provides "
                f"{item['interface']}."
            )

            lines.append(
                f"  Citation: "
                f"{item['citation']}"
            )

        return "\n".join(
            lines
        )

    # =========================================================
    # DEPENDENCY ANSWER
    # =========================================================

    def _generate_dependency_answer(
        self,
        evidence
    ):

        dependencies = []

        for result in evidence:

            metadata = result.get(
                "metadata",
                {}
            )

            if metadata.get(
                "entity_type"
            ) != "dependency":

                continue

            dependent = metadata.get(
                "dependent_component"
            )

            dependency = metadata.get(
                "dependency_component"
            )

            data_element = metadata.get(
                "data_element"
            )

            dependencies.append({
                "dependent":
                    dependent,
                "dependency":
                    dependency,
                "data_element":
                    data_element,
                "citation":
                    self._format_citation(
                        metadata
                    )
            })

        if not dependencies:

            return (
                "I could not find a directly "
                "supported dependency relationship "
                "in the retrieved architecture evidence."
            )

        lines = [
            "The architecture shows these dependencies:"
        ]

        seen = set()

        for item in dependencies:

            key = (
                item["dependent"],
                item["dependency"],
                item["data_element"]
            )

            if key in seen:
                continue

            seen.add(key)

            lines.append(
                f"- {item['dependent']} "
                f"depends on "
                f"{item['dependency']} "
                f"through "
                f"{item['data_element']}."
            )

            lines.append(
                f"  Citation: "
                f"{item['citation']}"
            )

        return "\n".join(
            lines
        )

    # =========================================================
    # FUNCTIONAL FLOW ANSWER
    # =========================================================

    def _generate_functional_flow_answer(
        self,
        evidence
    ):

        flows = []

        for result in evidence:

            metadata = result.get(
                "metadata",
                {}
            )

            if metadata.get(
                "entity_type"
            ) != "functional_flow":

                continue

            flows.append({
                "step":
                    metadata.get(
                        "step"
                    ),
                "description":
                    metadata.get(
                        "description"
                    ),
                "citation":
                    self._format_citation(
                        metadata
                    )
            })

        if not flows:

            return (
                "I could not find sufficient "
                "functional-flow evidence in "
                "the retrieved architecture."
            )

        flows.sort(
            key=lambda item:
            item["step"]
            if isinstance(
                item["step"],
                int
            )
            else 999
        )

        lines = [
            "The functional flow is:"
        ]

        for flow in flows:

            lines.append(
                f"- Step {flow['step']}: "
                f"{flow['description']}"
            )

            lines.append(
                f"  Citation: "
                f"{flow['citation']}"
            )

        return "\n".join(
            lines
        )

    # =========================================================
    # GENERAL ANSWER
    # =========================================================

    def _generate_general_answer(
        self,
        evidence
    ):

        if not evidence:

            return (
                "I could not find sufficient evidence "
                "in the indexed AUTOSAR HLD."
            )

        lines = [
            "Based on the retrieved HLD evidence:"
        ]

        for result in evidence[:5]:

            metadata = result.get(
                "metadata",
                {}
            )

            content = result.get(
                "content",
                ""
            )

            citation = (
                self._format_citation(
                    metadata
                )
            )

            lines.append(
                f"- {content}"
            )

            lines.append(
                f"  Citation: {citation}"
            )

        return "\n".join(
            lines
        )

    # =========================================================
    # MAIN GENERATION
    # =========================================================

    def generate(
        self,
        query,
        retrieved_results
    ):
        """
        Generate an evidence-grounded answer.
        """

        # -----------------------------------------------------
        # Step 1: Deduplicate retrieved evidence
        # -----------------------------------------------------

        evidence = (
            self._deduplicate_evidence(
                retrieved_results
            )
        )

        # -----------------------------------------------------
        # Step 2: Detect question intent
        # -----------------------------------------------------

        intent = (
            self._detect_intent(
                query
            )
        )

        # -----------------------------------------------------
        # Step 3: Apply query-specific filtering
        # -----------------------------------------------------

        filtered_evidence = (
            self._filter_evidence_for_query(
                query,
                evidence,
                intent
            )
        )

        # -----------------------------------------------------
        # Step 4: Generate answer
        # -----------------------------------------------------

        if intent == "interface":

            answer = (
                self._generate_interface_answer(
                    query,
                    filtered_evidence
                )
            )

        elif intent == "consume":

            answer = (
                self._generate_consumer_answer(
                    query,
                    filtered_evidence
                )
            )

        elif intent == "provide":

            answer = (
                self._generate_provider_answer(
                    filtered_evidence
                )
            )

        elif intent == "dependency":

            answer = (
                self._generate_dependency_answer(
                    filtered_evidence
                )
            )

        elif intent == "functional_flow":

            answer = (
                self._generate_functional_flow_answer(
                    filtered_evidence
                )
            )

        else:

            answer = (
                self._generate_general_answer(
                    filtered_evidence
                )
            )

        # -----------------------------------------------------
        # Step 5: Return result
        # -----------------------------------------------------

        return {
            "query": query,
            "answer": answer,
            "intent": intent,
            "evidence_count": len(
                filtered_evidence
            ),
            "evidence": filtered_evidence
        }

    # =========================================================
    # SAVE ANSWER
    # =========================================================

    def save_answer(
        self,
        output_path,
        result
    ):

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
                result,
                file,
                indent=2,
                ensure_ascii=False
            )

        return output_path