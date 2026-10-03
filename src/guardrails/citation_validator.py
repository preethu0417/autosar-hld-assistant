# src/guardrails/citation_validator.py

import re


class CitationValidator:
    """
    Validates whether citations in a generated answer
    are supported by the retrieved architecture evidence.
    """

    def __init__(self):
        pass

    # --------------------------------------------------
    # EXTRACT CITATIONS
    # --------------------------------------------------

    def extract_citations(
        self,
        answer
    ):
        """
        Extract citation strings from a generated answer.
        """

        pattern = re.compile(
            r"Citation:\s*(.+)"
        )

        citations = pattern.findall(
            answer
        )

        return [
            citation.strip()
            for citation in citations
        ]

    # --------------------------------------------------
    # BUILD EVIDENCE CITATIONS
    # --------------------------------------------------

    def _citation_from_metadata(
        self,
        metadata
    ):
        """
        Build the normalized citation string
        corresponding to retrieved evidence.
        """

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

    # --------------------------------------------------
    # VALIDATE CITATIONS
    # --------------------------------------------------

    def validate(
        self,
        answer,
        retrieved_results
    ):
        """
        Validate all citations in the answer against
        the retrieved evidence.
        """

        answer_citations = (
            self.extract_citations(
                answer
            )
        )

        supported_citations = []

        for result in retrieved_results:

            metadata = result.get(
                "metadata",
                {}
            )

            citation = (
                self._citation_from_metadata(
                    metadata
                )
            )

            supported_citations.append(
                citation
            )

        supported_set = set(
            supported_citations
        )

        validation_results = []

        for citation in answer_citations:

            is_supported = (
                citation in supported_set
            )

            validation_results.append({
                "citation": citation,
                "supported": is_supported
            })

        total_citations = len(
            answer_citations
        )

        supported_count = sum(
            item["supported"]
            for item in validation_results
        )

        if total_citations > 0:

            coverage = (
                supported_count
                / total_citations
            )

        else:

            coverage = 0.0

        return {
            "valid": (
                total_citations > 0
                and supported_count
                == total_citations
            ),
            "total_citations": total_citations,
            "supported_citations": supported_count,
            "citation_coverage": coverage,
            "details": validation_results
        }

    # --------------------------------------------------
    # ANSWER VALIDATION
    # --------------------------------------------------

    def validate_answer(
        self,
        answer,
        retrieved_results
    ):
        """
        Validate the generated answer and return
        a structured guardrail result.
        """

        validation = self.validate(
            answer,
            retrieved_results
        )

        if validation["valid"]:

            status = "PASS"

        else:

            status = "FAIL"

        return {
            "status": status,
            "valid": validation["valid"],
            "citation_coverage": validation[
                "citation_coverage"
            ],
            "total_citations": validation[
                "total_citations"
            ],
            "supported_citations": validation[
                "supported_citations"
            ],
            "details": validation[
                "details"
            ]
        }