# src/comparison/revision_compare.py

from pathlib import Path
import json


class RevisionComparator:
    """
    Compares two AUTOSAR architecture revisions.

    The comparison identifies:

    - Added entities
    - Removed entities
    - Changed entities
    - Unchanged entities

    Supported architecture entities:

    - Components
    - Ports
    - Interfaces
    - Data flows
    - Dependencies
    - Functional flows
    - Architecture relationships
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

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(
        self,
        old_architecture=None,
        new_architecture=None
    ):

        self.old_architecture = (
            old_architecture or {}
        )

        self.new_architecture = (
            new_architecture or {}
        )

    # =========================================================
    # LOAD JSON
    # =========================================================

    @staticmethod
    def load_architecture(
        architecture_path
    ):
        """
        Load architecture knowledge from JSON.
        """

        architecture_path = Path(
            architecture_path
        )

        if not architecture_path.exists():

            raise FileNotFoundError(
                f"Architecture file not found: "
                f"{architecture_path}"
            )

        with open(
            architecture_path,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    # =========================================================
    # SAVE JSON
    # =========================================================

    @staticmethod
    def save_comparison(
        output_path,
        comparison
    ):
        """
        Save comparison results to JSON.
        """

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
                comparison,
                file,
                indent=2,
                ensure_ascii=False
            )

        return output_path

    # =========================================================
    # ENTITY KEY
    # =========================================================

    def _entity_key(
        self,
        entity_type,
        entity
    ):
        """
        Create a stable identity for an architecture entity.

        Different entity types use different identity fields.
        """

        if not isinstance(
            entity,
            dict
        ):
            return str(entity)

        # -----------------------------------------------------
        # Components
        # -----------------------------------------------------

        if entity_type == "components":

            return (
                entity.get(
                    "name"
                )
                or entity.get(
                    "component"
                )
            )

        # -----------------------------------------------------
        # Ports
        # -----------------------------------------------------

        if entity_type == "ports":

            return (
                entity.get(
                    "name"
                )
                or entity.get(
                    "port"
                )
            )

        # -----------------------------------------------------
        # Interfaces
        # -----------------------------------------------------

        if entity_type == "interfaces":

            return (
                entity.get(
                    "name"
                )
                or entity.get(
                    "interface"
                )
            )

        # -----------------------------------------------------
        # Data flows
        # -----------------------------------------------------

        if entity_type == "data_flows":

            return (
                entity.get(
                    "signal"
                ),
                entity.get(
                    "relationship"
                ),
                entity.get(
                    "component"
                )
            )

        # -----------------------------------------------------
        # Dependencies
        # -----------------------------------------------------

        if entity_type == "dependencies":

            return (
                entity.get(
                    "dependent_component"
                ),
                entity.get(
                    "dependency_component"
                ),
                entity.get(
                    "data_element"
                )
            )

        # -----------------------------------------------------
        # Functional flows
        # -----------------------------------------------------

        if entity_type == "functional_flows":

            return (
                entity.get(
                    "step"
                ),
                entity.get(
                    "description"
                )
            )

        # -----------------------------------------------------
        # Architecture relationships
        # -----------------------------------------------------

        if entity_type == "architecture_relationships":

            return (
                entity.get(
                    "source_component"
                ),
                entity.get(
                    "target_component"
                ),
                entity.get(
                    "interface"
                )
            )

        # -----------------------------------------------------
        # Generic fallback
        # -----------------------------------------------------

        return json.dumps(
            entity,
            sort_keys=True,
            ensure_ascii=False
        )

    # =========================================================
    # NORMALIZE ENTITY
    # =========================================================

    def _normalize_entity(
        self,
        entity
    ):
        """
        Remove source-location metadata before comparing
        architecture content.

        Page and section changes should not by themselves
        be treated as architecture changes.
        """

        if not isinstance(
            entity,
            dict
        ):
            return entity

        ignored_fields = {
            "page",
            "section_number",
            "section_title",
            "document"
        }

        normalized = {}

        for key, value in entity.items():

            if key in ignored_fields:
                continue

            normalized[key] = value

        return normalized

    # =========================================================
    # ENTITY MAP
    # =========================================================

    def _build_entity_map(
        self,
        architecture,
        entity_type
    ):
        """
        Convert an entity list into:

        identity -> entity
        """

        entities = architecture.get(
            entity_type,
            []
        )

        entity_map = {}

        for entity in entities:

            key = self._entity_key(
                entity_type,
                entity
            )

            if key is None:
                continue

            entity_map[
                str(key)
            ] = entity

        return entity_map

    # =========================================================
    # COMPARE ENTITY TYPE
    # =========================================================

    def _compare_entity_type(
        self,
        entity_type
    ):
        """
        Compare one architecture entity category.
        """

        old_map = self._build_entity_map(
            self.old_architecture,
            entity_type
        )

        new_map = self._build_entity_map(
            self.new_architecture,
            entity_type
        )

        old_keys = set(
            old_map.keys()
        )

        new_keys = set(
            new_map.keys()
        )

        added_keys = (
            new_keys - old_keys
        )

        removed_keys = (
            old_keys - new_keys
        )

        common_keys = (
            old_keys & new_keys
        )

        added = []

        removed = []

        changed = []

        unchanged = []

        # -----------------------------------------------------
        # Added
        # -----------------------------------------------------

        for key in sorted(
            added_keys,
            key=str
        ):

            added.append(
                new_map[key]
            )

        # -----------------------------------------------------
        # Removed
        # -----------------------------------------------------

        for key in sorted(
            removed_keys,
            key=str
        ):

            removed.append(
                old_map[key]
            )

        # -----------------------------------------------------
        # Changed / unchanged
        # -----------------------------------------------------

        for key in sorted(
            common_keys,
            key=str
        ):

            old_entity = old_map[
                key
            ]

            new_entity = new_map[
                key
            ]

            old_normalized = (
                self._normalize_entity(
                    old_entity
                )
            )

            new_normalized = (
                self._normalize_entity(
                    new_entity
                )
            )

            if (
                old_normalized
                == new_normalized
            ):

                unchanged.append(
                    new_entity
                )

            else:

                changed.append({
                    "identity": key,
                    "old": old_entity,
                    "new": new_entity
                })

        return {
            "added": added,
            "removed": removed,
            "changed": changed,
            "unchanged": unchanged
        }

    # =========================================================
    # COMPARE
    # =========================================================

    def compare(self):
        """
        Compare the complete architecture.
        """

        comparison = {
            "summary": {},
            "changes": {}
        }

        total_added = 0
        total_removed = 0
        total_changed = 0
        total_unchanged = 0

        for entity_type in (
            self.ENTITY_TYPES
        ):

            result = (
                self._compare_entity_type(
                    entity_type
                )
            )

            comparison[
                "changes"
            ][entity_type] = result

            added_count = len(
                result["added"]
            )

            removed_count = len(
                result["removed"]
            )

            changed_count = len(
                result["changed"]
            )

            unchanged_count = len(
                result["unchanged"]
            )

            comparison[
                "summary"
            ][entity_type] = {
                "added": added_count,
                "removed": removed_count,
                "changed": changed_count,
                "unchanged": unchanged_count,
                "old_total": (
                    removed_count
                    + changed_count
                    + unchanged_count
                ),
                "new_total": (
                    added_count
                    + changed_count
                    + unchanged_count
                )
            }

            total_added += (
                added_count
            )

            total_removed += (
                removed_count
            )

            total_changed += (
                changed_count
            )

            total_unchanged += (
                unchanged_count
            )

        comparison[
            "summary"
        ]["overall"] = {
            "added": total_added,
            "removed": total_removed,
            "changed": total_changed,
            "unchanged": total_unchanged
        }

        return comparison

    # =========================================================
    # COMPARE FILES
    # =========================================================

    @classmethod
    def compare_files(
        cls,
        old_file,
        new_file,
        output_file=None
    ):
        """
        Compare two architecture JSON files.
        """

        old_architecture = (
            cls.load_architecture(
                old_file
            )
        )

        new_architecture = (
            cls.load_architecture(
                new_file
            )
        )

        comparator = cls(
            old_architecture,
            new_architecture
        )

        comparison = comparator.compare()

        if output_file is not None:

            cls.save_comparison(
                output_file,
                comparison
            )

        return comparison

    # =========================================================
    # HUMAN-READABLE REPORT
    # =========================================================

    def generate_report(
        self,
        comparison
    ):
        """
        Generate a human-readable revision comparison report.
        """

        lines = []

        lines.append(
            "AUTOSAR HLD REVISION COMPARISON"
        )

        lines.append(
            "=" * 45
        )

        overall = comparison[
            "summary"
        ].get(
            "overall",
            {}
        )

        lines.append(
            f"Added: {overall.get('added', 0)}"
        )

        lines.append(
            f"Removed: {overall.get('removed', 0)}"
        )

        lines.append(
            f"Changed: {overall.get('changed', 0)}"
        )

        lines.append(
            f"Unchanged: {overall.get('unchanged', 0)}"
        )

        lines.append("")

        # -----------------------------------------------------
        # Entity-by-entity report
        # -----------------------------------------------------

        for entity_type, result in (
            comparison[
                "changes"
            ].items()
        ):

            summary = comparison[
                "summary"
            ][entity_type]

            lines.append(
                entity_type.upper()
            )

            lines.append(
                "-" * 35
            )

            lines.append(
                f"Added: "
                f"{summary['added']}"
            )

            lines.append(
                f"Removed: "
                f"{summary['removed']}"
            )

            lines.append(
                f"Changed: "
                f"{summary['changed']}"
            )

            lines.append(
                f"Unchanged: "
                f"{summary['unchanged']}"
            )

            # -------------------------------------------------
            # Added
            # -------------------------------------------------

            for entity in result[
                "added"
            ]:

                lines.append(
                    f"  + ADDED: "
                    f"{self._display_entity(entity_type, entity)}"
                )

            # -------------------------------------------------
            # Removed
            # -------------------------------------------------

            for entity in result[
                "removed"
            ]:

                lines.append(
                    f"  - REMOVED: "
                    f"{self._display_entity(entity_type, entity)}"
                )

            # -------------------------------------------------
            # Changed
            # -------------------------------------------------

            for item in result[
                "changed"
            ]:

                lines.append(
                    f"  ~ CHANGED: "
                    f"{item['identity']}"
                )

                lines.append(
                    f"    OLD: "
                    f"{self._display_entity(
                        entity_type,
                        item['old']
                    )}"
                )

                lines.append(
                    f"    NEW: "
                    f"{self._display_entity(
                        entity_type,
                        item['new']
                    )}"
                )

            lines.append("")

        return "\n".join(
            lines
        )

    # =========================================================
    # DISPLAY ENTITY
    # =========================================================

    def _display_entity(
        self,
        entity_type,
        entity
    ):
        """
        Create a compact human-readable representation.
        """

        if not isinstance(
            entity,
            dict
        ):

            return str(
                entity
            )

        if entity_type == "components":

            return str(
                entity.get(
                    "name",
                    entity
                )
            )

        if entity_type == "ports":

            return str(
                entity.get(
                    "name",
                    entity
                )
            )

        if entity_type == "interfaces":

            name = entity.get(
                "name",
                ""
            )

            provider = entity.get(
                "provider",
                ""
            )

            consumer = entity.get(
                "consumer",
                ""
            )

            return (
                f"{name} "
                f"({provider} -> {consumer})"
            )

        if entity_type == "data_flows":

            return (
                f"{entity.get('signal', '')} "
                f"{entity.get('relationship', '')} "
                f"{entity.get('component', '')}"
            )

        if entity_type == "dependencies":

            return (
                f"{entity.get('dependent_component', '')} "
                f"depends on "
                f"{entity.get('dependency_component', '')} "
                f"through "
                f"{entity.get('data_element', '')}"
            )

        if entity_type == "functional_flows":

            return (
                f"Step {entity.get('step', '')}: "
                f"{entity.get('description', '')}"
            )

        if entity_type == "architecture_relationships":

            return (
                f"{entity.get('source_component', '')} "
                f"-> "
                f"{entity.get('target_component', '')} "
                f"through "
                f"{entity.get('interface', '')}"
            )

        return str(
            entity
        )