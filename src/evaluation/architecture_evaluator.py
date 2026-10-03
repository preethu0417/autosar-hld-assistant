# src/evaluation/architecture_evaluator.py

from pathlib import Path
import json


class ArchitectureEvaluator:
    """
    Evaluates extracted AUTOSAR architecture knowledge
    against a reference architecture.

    Supported entity types:
    - components
    - ports
    - interfaces
    - data_flows
    - dependencies
    - functional_flows
    - architecture_relationships
    """

    ENTITY_TYPES = [
        "components",
        "ports",
        "interfaces",
        "data_flows",
        "dependencies",
        "functional_flows",
        "architecture_relationships"
    ]

    def __init__(
        self,
        predicted_architecture,
        reference_architecture
    ):
        self.predicted = predicted_architecture
        self.reference = reference_architecture

    # --------------------------------------------------
    # ENTITY NORMALIZATION
    # --------------------------------------------------

    def _normalize_text(self, value):
        """
        Normalize text for reliable comparison.
        """

        if value is None:
            return ""

        value = str(value)

        return " ".join(
            value.strip().lower().split()
        )

    def _normalize_entity(
        self,
        entity_type,
        entity
    ):
        """
        Convert an architecture entity into a
        comparable representation.
        """

        if entity_type == "components":

            return (
                self._normalize_text(
                    entity.get("name")
                ),
            )

        if entity_type == "ports":

            return (
                self._normalize_text(
                    entity.get("name")
                ),
            )

        if entity_type == "interfaces":

            return (
                self._normalize_text(
                    entity.get("name")
                ),
                self._normalize_text(
                    entity.get("provider")
                ),
                self._normalize_text(
                    entity.get("consumer")
                ),
                tuple(
                    sorted(
                        self._normalize_text(item)
                        for item in entity.get(
                            "data_elements",
                            []
                        )
                    )
                )
            )

        if entity_type == "data_flows":

            return (
                self._normalize_text(
                    entity.get("signal")
                ),
                self._normalize_text(
                    entity.get("relationship")
                ),
                self._normalize_text(
                    entity.get("component")
                )
            )

        if entity_type == "dependencies":

            return (
                self._normalize_text(
                    entity.get(
                        "dependent_component"
                    )
                ),
                self._normalize_text(
                    entity.get(
                        "dependency_component"
                    )
                ),
                self._normalize_text(
                    entity.get(
                        "data_element"
                    )
                )
            )

        if entity_type == "functional_flows":

            description = self._normalize_text(
                entity.get("description")
            )

            return (
                entity.get("step"),
                description
            )

        if entity_type == (
            "architecture_relationships"
        ):

            return (
                self._normalize_text(
                    entity.get(
                        "source_component"
                    )
                ),
                self._normalize_text(
                    entity.get(
                        "target_component"
                    )
                ),
                self._normalize_text(
                    entity.get("interface")
                )
            )

        return (
            json.dumps(
                entity,
                sort_keys=True
            ),
        )

    # --------------------------------------------------
    # ENTITY SETS
    # --------------------------------------------------

    def _entity_sets(
        self,
        entity_type
    ):
        """
        Build predicted and reference sets.
        """

        predicted_entities = (
            self.predicted.get(
                entity_type,
                []
            )
        )

        reference_entities = (
            self.reference.get(
                entity_type,
                []
            )
        )

        predicted_set = {
            self._normalize_entity(
                entity_type,
                entity
            )
            for entity in predicted_entities
        }

        reference_set = {
            self._normalize_entity(
                entity_type,
                entity
            )
            for entity in reference_entities
        }

        return (
            predicted_set,
            reference_set
        )

    # --------------------------------------------------
    # PRECISION / RECALL / F1
    # --------------------------------------------------

    def evaluate_entity(
        self,
        entity_type
    ):
        """
        Calculate precision, recall and F1
        for one architecture entity type.
        """

        predicted_set, reference_set = (
            self._entity_sets(
                entity_type
            )
        )

        true_positive = len(
            predicted_set
            & reference_set
        )

        false_positive = len(
            predicted_set
            - reference_set
        )

        false_negative = len(
            reference_set
            - predicted_set
        )

        if (
            true_positive
            + false_positive
        ) > 0:

            precision = (
                true_positive
                /
                (
                    true_positive
                    + false_positive
                )
            )

        else:

            precision = 1.0 if not reference_set else 0.0

        if (
            true_positive
            + false_negative
        ) > 0:

            recall = (
                true_positive
                /
                (
                    true_positive
                    + false_negative
                )
            )

        else:

            recall = 1.0

        if (
            precision
            + recall
        ) > 0:

            f1 = (
                2
                * precision
                * recall
                /
                (
                    precision
                    + recall
                )
            )

        else:

            f1 = 0.0

        return {
            "entity_type": entity_type,
            "true_positive": true_positive,
            "false_positive": false_positive,
            "false_negative": false_negative,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "predicted_count": len(
                predicted_set
            ),
            "reference_count": len(
                reference_set
            )
        }

    # --------------------------------------------------
    # ALL ENTITY METRICS
    # --------------------------------------------------

    def evaluate_all(self):
        """
        Evaluate every supported architecture entity.
        """

        results = {}

        for entity_type in self.ENTITY_TYPES:

            results[entity_type] = (
                self.evaluate_entity(
                    entity_type
                )
            )

        return results

    # --------------------------------------------------
    # MACRO METRICS
    # --------------------------------------------------

    def macro_metrics(
        self,
        results=None
    ):
        """
        Calculate macro-average precision,
        recall and F1 across entity types.
        """

        if results is None:

            results = self.evaluate_all()

        if not results:

            return {
                "precision": 0.0,
                "recall": 0.0,
                "f1": 0.0
            }

        precision = sum(
            result["precision"]
            for result in results.values()
        ) / len(results)

        recall = sum(
            result["recall"]
            for result in results.values()
        ) / len(results)

        f1 = sum(
            result["f1"]
            for result in results.values()
        ) / len(results)

        return {
            "precision": precision,
            "recall": recall,
            "f1": f1
        }

    # --------------------------------------------------
    # COMPLETENESS
    # --------------------------------------------------

    def completeness(
        self,
        results=None
    ):
        """
        Calculate overall extraction completeness
        based on reference entities correctly recovered.
        """

        if results is None:

            results = self.evaluate_all()

        total_reference = sum(
            result["reference_count"]
            for result in results.values()
        )

        total_true_positive = sum(
            result["true_positive"]
            for result in results.values()
        )

        if total_reference == 0:

            return 1.0

        return (
            total_true_positive
            /
            total_reference
        )

    # --------------------------------------------------
    # CONSISTENCY CHECK
    # --------------------------------------------------

    def consistency_check(self):
        """
        Check architecture references for missing
        internal components and identify external entities.
        """

        components = {
            self._normalize_text(
                component.get("name")
            )
            for component in self.predicted.get(
                "components",
                []
            )
        }

        referenced_entities = set()

        for dependency in self.predicted.get(
            "dependencies",
            []
        ):

            referenced_entities.add(
                self._normalize_text(
                    dependency.get(
                        "dependent_component"
                    )
                )
            )

            referenced_entities.add(
                self._normalize_text(
                    dependency.get(
                        "dependency_component"
                    )
                )
            )

        for relationship in self.predicted.get(
            "architecture_relationships",
            []
        ):

            referenced_entities.add(
                self._normalize_text(
                    relationship.get(
                        "source_component"
                    )
                )
            )

            referenced_entities.add(
                self._normalize_text(
                    relationship.get(
                        "target_component"
                    )
                )
            )

        missing_internal = sorted(
            referenced_entities
            - components
            - {"coolingsystem"}
        )

        external_entities = sorted(
            referenced_entities
            - components
        )

        return {
            "status": (
                "PASS"
                if not missing_internal
                else "REVIEW"
            ),
            "external_entities": [
                item
                for item in external_entities
                if item not in {
                    "coolingsystem"
                }
            ],
            "known_external_entities": [
                item
                for item in external_entities
                if item in {
                    "coolingsystem"
                }
            ],
            "missing_internal_entities": (
                missing_internal
            ),
            "total_issues": len(
                missing_internal
            )
        }

    # --------------------------------------------------
    # COMPLETE EVALUATION
    # --------------------------------------------------

    def evaluate(self):
        """
        Generate the complete architecture
        evaluation report.
        """

        entity_results = (
            self.evaluate_all()
        )

        macro = self.macro_metrics(
            entity_results
        )

        completeness = (
            self.completeness(
                entity_results
            )
        )

        consistency = (
            self.consistency_check()
        )

        return {
            "entity_metrics": entity_results,
            "macro_metrics": macro,
            "overall_completeness": completeness,
            "consistency": consistency
        }

    # --------------------------------------------------
    # SAVE
    # --------------------------------------------------

    def save(
        self,
        output_path,
        evaluation=None
    ):
        """
        Save evaluation results as JSON.
        """

        if evaluation is None:

            evaluation = self.evaluate()

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
                evaluation,
                file,
                indent=2,
                ensure_ascii=False
            )

        return output_path