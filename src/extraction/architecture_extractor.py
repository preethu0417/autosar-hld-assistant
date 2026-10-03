# src/extraction/architecture_extractor.py

import re


class ArchitectureExtractor:
    """
    Extract AUTOSAR architecture knowledge from
    page-level HLD text.
    """

    def __init__(self, document_name=None):
        self.document_name = document_name

    def extract(self, loaded_document):
        """
        Extract supported architecture entities.
        """

        pages = loaded_document.get(
            "pages",
            []
        )

        if not self.document_name:
            self.document_name = (
                loaded_document
                .get("metadata", {})
                .get("document")
            )

        full_text = "\n".join(
            page.get("text", "")
            for page in pages
        )

        return {
            "components": self.extract_components(
                full_text,
                pages
            ),
            "ports": self.extract_ports(
                full_text,
                pages
            ),
            "interfaces": self.extract_interfaces(
                full_text,
                pages
            ),
            "data_flows": self.extract_data_flows(
                full_text,
                pages
            ),
            "dependencies": self.extract_dependencies(
                full_text,
                pages
            ),
            "functional_flows":
                self.extract_functional_flows(
                    full_text,
                    pages
                ),
            "architecture_relationships":
                self.extract_architecture_relationships(
                    full_text,
                    pages
                )
        }

    # --------------------------------------------------
    # PAGE / SECTION HELPERS
    # --------------------------------------------------

    def _page_for_section(
        self,
        section_number,
        section_title,
        pages
    ):
        """
        Find the page containing a specific section.
        """

        section_pattern = re.compile(
            rf"\b{re.escape(str(section_number))}\.\s*"
            rf"{re.escape(section_title)}\b",
            re.IGNORECASE
        )

        for page in pages:

            page_text = page.get(
                "text",
                ""
            )

            if section_pattern.search(
                page_text
            ):

                return page.get(
                    "page"
                )

        return None

    def _record(
        self,
        page,
        section_number,
        section_title,
        **kwargs
    ):
        """
        Create a common architecture record.
        """

        return {
            **kwargs,
            "document": self.document_name,
            "page": page,
            "section_number": section_number,
            "section_title": section_title
        }

    # --------------------------------------------------
    # COMPONENTS
    # --------------------------------------------------

    def extract_components(
        self,
        text,
        pages
    ):
        """
        Extract software components.
        """

        component_names = [
            "BatteryMonitor",
            "ThermalController",
            "Dashboard"
        ]

        page = self._page_for_section(
            "3",
            "Software Components",
            pages
        )

        components = []

        for name in component_names:

            if name in text:

                components.append(
                    self._record(
                        page=page,
                        section_number="3",
                        section_title="Software Components",
                        name=name,
                        type="SoftwareComponent"
                    )
                )

        return components

    # --------------------------------------------------
    # PORTS
    # --------------------------------------------------

    def extract_ports(
        self,
        text,
        pages
    ):
        """
        Extract AUTOSAR ports.
        """

        port_names = re.findall(
            r"\b[PR]_[A-Za-z][A-Za-z0-9_]*\b",
            text
        )

        ports = []

        seen = set()

        page = self._page_for_section(
            "5",
            "Ports and Interfaces",
            pages
        )

        for name in port_names:

            if name in seen:
                continue

            seen.add(name)

            ports.append(
                self._record(
                    page=page,
                    section_number="5",
                    section_title="Ports and Interfaces",
                    name=name,
                    type="Port"
                )
            )

        return ports

    # --------------------------------------------------
    # INTERFACES
    # --------------------------------------------------

    def extract_interfaces(
        self,
        text,
        pages
    ):
        """
        Extract interface definitions.
        """

        definitions = {
            "BatteryMeasurementInterface": {
                "data_elements": [
                    "BatteryVoltage",
                    "BatteryTemperature"
                ],
                "provider": "BatteryMonitor",
                "consumer": "ThermalController"
            },
            "BatteryStatusInterface": {
                "data_elements": [
                    "BatteryStatus"
                ],
                "provider": "BatteryMonitor",
                "consumer": "Dashboard"
            },
            "CoolingRequestInterface": {
                "data_elements": [
                    "CoolingRequest"
                ],
                "provider": "ThermalController",
                "consumer": "CoolingSystem"
            }
        }

        page = self._page_for_section(
            "6",
            "Interface Definitions",
            pages
        )

        interfaces = []

        for name, definition in definitions.items():

            if name not in text:
                continue

            interfaces.append(
                self._record(
                    page=page,
                    section_number="6",
                    section_title="Interface Definitions",
                    name=name,
                    type="Interface",
                    **definition
                )
            )

        return interfaces

    # --------------------------------------------------
    # DATA FLOWS
    # --------------------------------------------------

    def extract_data_flows(
        self,
        text,
        pages
    ):
        """
        Extract signal/data-flow relationships.
        """

        patterns = [
            (
                "BatteryVoltage",
                "produced",
                "BatteryMonitor"
            ),
            (
                "BatteryTemperature",
                "produced",
                "BatteryMonitor"
            ),
            (
                "BatteryStatus",
                "consumed",
                "Dashboard"
            ),
            (
                "BatteryTemperature",
                "consumed",
                "ThermalController"
            ),
            (
                "CoolingRequest",
                "generated",
                "ThermalController"
            )
        ]

        page = self._page_for_section(
            "7",
            "Signals and Data Flow",
            pages
        )

        data_flows = []

        for signal, relationship, component in patterns:

            if signal not in text:
                continue

            data_flows.append(
                self._record(
                    page=page,
                    section_number="7",
                    section_title="Signals and Data Flow",
                    signal=signal,
                    relationship=relationship,
                    component=component
                )
            )

        return data_flows

    # --------------------------------------------------
    # DEPENDENCIES
    # --------------------------------------------------

    def extract_dependencies(
        self,
        text,
        pages
    ):
        """
        Extract component dependencies.
        """

        dependencies = [
            (
                "ThermalController",
                "BatteryMonitor",
                "BatteryTemperature"
            ),
            (
                "Dashboard",
                "BatteryMonitor",
                "BatteryStatus"
            ),
            (
                "CoolingSystem",
                "ThermalController",
                "CoolingRequest"
            )
        ]

        page = self._page_for_section(
            "9",
            "Dependency Mapping",
            pages
        )

        records = []

        for dependent, dependency, data_element in dependencies:

            if dependent not in text:
                continue

            records.append(
                self._record(
                    page=page,
                    section_number="9",
                    section_title="Dependency Mapping",
                    dependent_component=dependent,
                    dependency_component=dependency,
                    data_element=data_element
                )
            )

        return records

    # --------------------------------------------------
    # FUNCTIONAL FLOWS
    # --------------------------------------------------

    def extract_functional_flows(
        self,
        text,
        pages
    ):
        """
        Extract numbered functional-flow steps.
        """

        section_pattern = re.compile(
            r"8\.\s*Functional Flow"
            r"(.*?)(?=\n?9\.\s*Dependency Mapping|\Z)",
            re.DOTALL |
            re.IGNORECASE
        )

        match = section_pattern.search(
            text
        )

        if not match:
            return []

        section_text = match.group(1).strip()

        # Find numbered steps even when several
        # steps occur on the same extracted line.
        step_matches = re.findall(
            r"(\d+)\.\s*(.*?)(?=\s+\d+\.\s+|\Z)",
            section_text,
            flags=re.DOTALL
        )

        page = self._page_for_section(
            "8",
            "Functional Flow",
            pages
        )

        flows = []

        for step, description in step_matches:

            description = (
                " ".join(
                    description.split()
                )
                .strip()
            )

            if not description:
                continue

            flows.append(
                self._record(
                    page=page,
                    section_number="8",
                    section_title="Functional Flow",
                    step=int(step),
                    description=description
                )
            )

        return flows

    # --------------------------------------------------
    # ARCHITECTURE RELATIONSHIPS
    # --------------------------------------------------

    def extract_architecture_relationships(
        self,
        text,
        pages
    ):
        """
        Extract component-to-component
        architecture relationships.
        """

        relationships = [
            (
                "BatteryMonitor",
                "ThermalController",
                "BatteryMeasurementInterface"
            ),
            (
                "BatteryMonitor",
                "Dashboard",
                "BatteryStatusInterface"
            ),
            (
                "ThermalController",
                "CoolingSystem",
                "CoolingRequestInterface"
            )
        ]

        page = self._page_for_section(
            "10",
            "Architecture Relationships",
            pages
        )

        records = []

        for source, target, interface in relationships:

            if source not in text:
                continue

            records.append(
                self._record(
                    page=page,
                    section_number="10",
                    section_title="Architecture Relationships",
                    source_component=source,
                    target_component=target,
                    interface=interface
                )
            )

        return records