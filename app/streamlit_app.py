# app/streamlit_app.py

from pathlib import Path
import sys
import json

import streamlit as st
import pandas as pd


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# PROJECT IMPORTS
# ============================================================

from src.retrieval.retriever import ArchitectureRetriever
from src.generation.answer_generator import ArchitectureAnswerGenerator
from src.comparison.revision_compare import RevisionComparator


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="AUTOSAR HLD Analysis Assistant",
    page_icon="🚗",
    layout="wide"
)


# ============================================================
# FILE PATHS
# ============================================================

ARCHITECTURE_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "extracted_entities"
    / "architecture_knowledge.json"
)

RAG_INDEX_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "rag_index"
    / "autosar_hld.faiss"
)

RAG_DOCUMENTS_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "rag_index"
    / "rag_documents.json"
)

EVALUATION_FILE = (
    PROJECT_ROOT
    / "eval"
    / "results"
    / "notebook05_architecture_evaluation.json"
)

RETRIEVAL_EVALUATION_FILE = (
    PROJECT_ROOT
    / "eval"
    / "results"
    / "notebook04_retrieval_evaluation.json"
)

RETRIEVAL_METRICS_FILE = (
    PROJECT_ROOT
    / "eval"
    / "results"
    / "notebook04_retrieval_metrics.csv"
)

ARCHITECTURE_METRICS_FILE = (
    PROJECT_ROOT
    / "eval"
    / "results"
    / "notebook05_architecture_metrics.csv"
)

COMPARISON_DIRECTORY = (
    PROJECT_ROOT
    / "outputs"
    / "comparison"
)

COMPARISON_DIRECTORY.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# LOAD ARCHITECTURE
# ============================================================

@st.cache_data
def load_architecture():

    if not ARCHITECTURE_FILE.exists():
        return {}

    with open(
        ARCHITECTURE_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# ============================================================
# LOAD RAG SYSTEM
# ============================================================

@st.cache_resource
def load_rag_system():

    if not RAG_INDEX_FILE.exists():

        raise FileNotFoundError(
            f"FAISS index not found:\n"
            f"{RAG_INDEX_FILE}"
        )

    if not RAG_DOCUMENTS_FILE.exists():

        raise FileNotFoundError(
            f"RAG documents not found:\n"
            f"{RAG_DOCUMENTS_FILE}"
        )

    retriever = ArchitectureRetriever()

    retriever.load_index(
        RAG_INDEX_FILE,
        RAG_DOCUMENTS_FILE
    )

    generator = ArchitectureAnswerGenerator()

    return retriever, generator


# ============================================================
# LOAD EVALUATION
# ============================================================

@st.cache_data
def load_evaluation():

    if not EVALUATION_FILE.exists():
        return {}

    with open(
        EVALUATION_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# ============================================================
# CITATION
# ============================================================

def format_citation(metadata):

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


# ============================================================
# DISPLAY RETRIEVED EVIDENCE
# ============================================================

def render_evidence(evidence):

    if not evidence:

        st.info(
            "No supporting architecture evidence "
            "was retrieved."
        )

        return

    st.subheader(
        "Retrieved Evidence"
    )

    for number, item in enumerate(
        evidence,
        start=1
    ):

        metadata = item.get(
            "metadata",
            {}
        )

        entity_type = metadata.get(
            "entity_type",
            "unknown"
        )

        score = item.get(
            "score",
            0
        )

        retrieval_type = item.get(
            "retrieval_type",
            "unknown"
        )

        with st.expander(
            f"Evidence {number} — {entity_type}"
        ):

            st.write(
                item.get(
                    "content",
                    ""
                )
            )

            col1, col2 = st.columns(2)

            with col1:

                st.caption(
                    f"Retrieval type: "
                    f"{retrieval_type}"
                )

            with col2:

                if isinstance(
                    score,
                    (float, int)
                ):

                    st.caption(
                        f"Score: {score:.4f}"
                    )

                else:

                    st.caption(
                        f"Score: {score}"
                    )

            st.caption(
                "📄 "
                + format_citation(
                    metadata
                )
            )


# ============================================================
# LOAD UPLOADED JSON
# ============================================================

def load_uploaded_json(
    uploaded_file
):

    if uploaded_file is None:
        return None

    try:

        content = uploaded_file.getvalue()

        return json.loads(
            content.decode("utf-8")
        )

    except Exception as error:

        st.error(
            f"Unable to read "
            f"{uploaded_file.name}: {error}"
        )

        return None


# ============================================================
# REVISION SUMMARY
# ============================================================

def display_revision_summary(
    comparison
):

    overall = (
        comparison
        .get("summary", {})
        .get("overall", {})
    )

    added = overall.get(
        "added",
        0
    )

    removed = overall.get(
        "removed",
        0
    )

    changed = overall.get(
        "changed",
        0
    )

    unchanged = overall.get(
        "unchanged",
        0
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Added",
            added
        )

    with col2:

        st.metric(
            "Removed",
            removed
        )

    with col3:

        st.metric(
            "Changed",
            changed
        )

    with col4:

        st.metric(
            "Unchanged",
            unchanged
        )


# ============================================================
# DISPLAY ENTITY CHANGES
# ============================================================

def display_entity_changes(
    entity_type,
    result
):

    added = result.get(
        "added",
        []
    )

    removed = result.get(
        "removed",
        []
    )

    changed = result.get(
        "changed",
        []
    )

    unchanged = result.get(
        "unchanged",
        []
    )

    # --------------------------------------------------------
    # NO CHANGES
    # --------------------------------------------------------

    if (
        not added
        and not removed
        and not changed
    ):

        st.success(
            "No architecture changes detected."
        )

        st.caption(
            f"Unchanged entities: "
            f"{len(unchanged)}"
        )

        return

    comparator = RevisionComparator(
        {},
        {}
    )

    # --------------------------------------------------------
    # ADDED
    # --------------------------------------------------------

    if added:

        st.markdown(
            "#### Added"
        )

        for entity in added:

            display_text = (
                comparator._display_entity(
                    entity_type,
                    entity
                )
            )

            st.write(
                f"🟢 {display_text}"
            )

    # --------------------------------------------------------
    # REMOVED
    # --------------------------------------------------------

    if removed:

        st.markdown(
            "#### Removed"
        )

        for entity in removed:

            display_text = (
                comparator._display_entity(
                    entity_type,
                    entity
                )
            )

            st.write(
                f"🔴 {display_text}"
            )

    # --------------------------------------------------------
    # CHANGED
    # --------------------------------------------------------

    if changed:

        st.markdown(
            "#### Changed"
        )

        for item in changed:

            identity = item.get(
                "identity",
                "Unknown"
            )

            st.write(
                f"🟡 {identity}"
            )

            old_entity = item.get(
                "old",
                {}
            )

            new_entity = item.get(
                "new",
                {}
            )

            col1, col2 = st.columns(2)

            with col1:

                st.markdown(
                    "**Previous Revision**"
                )

                st.json(
                    old_entity
                )

            with col2:

                st.markdown(
                    "**New Revision**"
                )

                st.json(
                    new_entity
                )

    # --------------------------------------------------------
    # UNCHANGED
    # --------------------------------------------------------

    if unchanged:

        st.caption(
            f"Unchanged entities: "
            f"{len(unchanged)}"
        )


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title(
    "Navigation"
)

module = st.sidebar.radio(
    "Select module",
    [
        "Architecture Overview",
        "Ask Architecture",
        "Revision Comparison",
        "Evaluation",
        "Reports"
    ]
)

st.sidebar.divider()

st.sidebar.markdown(
    "**AUTOSAR HLD Assistant**"
)

st.sidebar.caption(
    "Pilot Demonstration"
)


# ============================================================
# HEADER
# ============================================================

st.title(
    "AUTOSAR HLD Analysis Assistant"
)

st.caption(
    "AI-assisted architecture analysis, "
    "search, validation and revision comparison"
)


# ============================================================
# LOAD MAIN ARCHITECTURE
# ============================================================

architecture = load_architecture()


# ============================================================
# 1. ARCHITECTURE OVERVIEW
# ============================================================

if module == "Architecture Overview":

    st.header(
        "Architecture Overview"
    )

    st.write(
        "Structured architecture knowledge "
        "extracted from the AUTOSAR HLD."
    )

    components = architecture.get(
        "components",
        []
    )

    ports = architecture.get(
        "ports",
        []
    )

    interfaces = architecture.get(
        "interfaces",
        []
    )

    data_flows = architecture.get(
        "data_flows",
        []
    )

    dependencies = architecture.get(
        "dependencies",
        []
    )

    functional_flows = architecture.get(
        "functional_flows",
        []
    )

    relationships = architecture.get(
        "architecture_relationships",
        []
    )

    # --------------------------------------------------------
    # METRICS
    # --------------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Components",
            len(components)
        )

    with col2:

        st.metric(
            "Ports",
            len(ports)
        )

    with col3:

        st.metric(
            "Interfaces",
            len(interfaces)
        )

    with col4:

        st.metric(
            "Dependencies",
            len(dependencies)
        )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Data Flows",
            len(data_flows)
        )

    with col2:

        st.metric(
            "Functional Flows",
            len(functional_flows)
        )

    with col3:

        st.metric(
            "Architecture Relationships",
            len(relationships)
        )

    st.divider()

    # --------------------------------------------------------
    # COMPONENTS
    # --------------------------------------------------------

    st.subheader(
        "Software Components"
    )

    component_rows = []

    for component in components:

        component_rows.append({
            "Component": component.get(
                "name",
                ""
            ),
            "Type": component.get(
                "type",
                ""
            ),
            "Role": component.get(
                "role",
                ""
            ),
            "Page": component.get(
                "page",
                ""
            )
        })

    if component_rows:

        st.dataframe(
            pd.DataFrame(component_rows),
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No components available."
        )

    # --------------------------------------------------------
    # INTERFACES
    # --------------------------------------------------------

    st.subheader(
        "Interfaces"
    )

    interface_rows = []

    for interface in interfaces:

        interface_rows.append({
            "Interface": interface.get(
                "name",
                ""
            ),
            "Provider": interface.get(
                "provider",
                ""
            ),
            "Consumer": interface.get(
                "consumer",
                ""
            ),
            "Data Elements": ", ".join(
                interface.get(
                    "data_elements",
                    []
                )
            ),
            "Page": interface.get(
                "page",
                ""
            )
        })

    if interface_rows:

        st.dataframe(
            pd.DataFrame(interface_rows),
            use_container_width=True,
            hide_index=True
        )

    # --------------------------------------------------------
    # DEPENDENCIES
    # --------------------------------------------------------

    st.subheader(
        "Dependencies"
    )

    dependency_rows = []

    for dependency in dependencies:

        dependency_rows.append({
            "Dependent Component": dependency.get(
                "dependent_component",
                ""
            ),
            "Dependency Component": dependency.get(
                "dependency_component",
                ""
            ),
            "Data Element": dependency.get(
                "data_element",
                ""
            ),
            "Page": dependency.get(
                "page",
                ""
            )
        })

    if dependency_rows:

        st.dataframe(
            pd.DataFrame(dependency_rows),
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# 2. ASK ARCHITECTURE
# ============================================================

elif module == "Ask Architecture":

    st.header(
        "Ask Architecture"
    )

    st.write(
        "Ask questions about the extracted "
        "AUTOSAR architecture."
    )

    question = st.text_input(
        "Architecture question",
        placeholder=(
            "Example: Which component consumes "
            "BatteryTemperature?"
        )
    )

    search_button = st.button(
        "Search Architecture",
        type="primary"
    )

    if search_button:

        if not question.strip():

            st.warning(
                "Please enter an architecture question."
            )

        else:

            try:

                with st.spinner(
                    "Retrieving architecture evidence..."
                ):

                    retriever, generator = (
                        load_rag_system()
                    )

                    retrieved_results = (
                        retriever.hybrid_search(
                            question,
                            top_k=5
                        )
                    )

                    result = generator.generate(
                        question,
                        retrieved_results
                    )

                st.divider()

                # ------------------------------------------------
                # ANSWER
                # ------------------------------------------------

                st.subheader(
                    "Answer"
                )

                st.markdown(
                    result.get(
                        "answer",
                        ""
                    )
                )

                # ------------------------------------------------
                # METRICS
                # ------------------------------------------------

                col1, col2, col3 = st.columns(3)

                with col1:

                    st.metric(
                        "Question Type",
                        result.get(
                            "intent",
                            "general"
                        )
                    )

                with col2:

                    st.metric(
                        "Evidence Items",
                        result.get(
                            "evidence_count",
                            0
                        )
                    )

                with col3:

                    citation_count = sum(
                        "Citation:" in line
                        for line in result.get(
                            "answer",
                            ""
                        ).splitlines()
                    )

                    st.metric(
                        "Citations",
                        citation_count
                    )

                # ------------------------------------------------
                # CITATION STATUS
                # ------------------------------------------------

                evidence = result.get(
                    "evidence",
                    []
                )

                if (
                    citation_count > 0
                    and evidence
                ):

                    st.success(
                        "Evidence-grounded answer "
                        "with citations."
                    )

                elif evidence:

                    st.warning(
                        "Evidence was retrieved, "
                        "but no citation was detected."
                    )

                else:

                    st.warning(
                        "No supporting evidence was retrieved."
                    )

                # ------------------------------------------------
                # EVIDENCE
                # ------------------------------------------------

                render_evidence(
                    evidence
                )

                # ------------------------------------------------
                # ENGINEERING REVIEW
                # ------------------------------------------------

                st.info(
                    "Engineering review is required before "
                    "using AI-assisted results for architecture "
                    "approval, software release, compliance, "
                    "or vehicle validation."
                )

            except Exception as error:

                st.error(
                    "Unable to process the architecture query."
                )

                st.exception(
                    error
                )


# ============================================================
# 3. REVISION COMPARISON
# ============================================================

elif module == "Revision Comparison":

    st.header(
        "Revision Comparison"
    )

    st.write(
        "Compare two AUTOSAR architecture revisions "
        "and identify added, removed, changed and "
        "unchanged architecture entities."
    )

    st.info(
        "Upload architecture JSON files generated "
        "by the HLD extraction pipeline."
    )

    # --------------------------------------------------------
    # UPLOAD FILES
    # --------------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:

        st.subheader(
            "Previous Revision"
        )

        old_file = st.file_uploader(
            "Upload previous architecture JSON",
            type=["json"],
            key="old_revision_file"
        )

    with col2:

        st.subheader(
            "New Revision"
        )

        new_file = st.file_uploader(
            "Upload new architecture JSON",
            type=["json"],
            key="new_revision_file"
        )

    st.divider()

    # --------------------------------------------------------
    # USE CURRENT ARCHITECTURE
    # --------------------------------------------------------

    use_current = st.checkbox(
        "Use current architecture_knowledge.json "
        "as the previous revision"
    )

    if use_current:

        if ARCHITECTURE_FILE.exists():

            old_architecture = (
                load_architecture()
            )

            st.success(
                "Current architecture loaded as "
                "the previous revision."
            )

        else:

            old_architecture = None

            st.error(
                "architecture_knowledge.json "
                "was not found."
            )

    else:

        old_architecture = (
            load_uploaded_json(
                old_file
            )
        )

    new_architecture = (
        load_uploaded_json(
            new_file
        )
    )

    # --------------------------------------------------------
    # COMPARE
    # --------------------------------------------------------

    compare_button = st.button(
        "Compare Revisions",
        type="primary"
    )

    if compare_button:

        if old_architecture is None:

            st.error(
                "Please provide the previous revision."
            )

        elif new_architecture is None:

            st.error(
                "Please provide the new revision."
            )

        else:

            try:

                with st.spinner(
                    "Comparing architecture revisions..."
                ):

                    comparator = RevisionComparator(
                        old_architecture,
                        new_architecture
                    )

                    comparison = (
                        comparator.compare()
                    )

                st.success(
                    "Revision comparison completed successfully."
                )

                st.divider()

                # ------------------------------------------------
                # SUMMARY
                # ------------------------------------------------

                st.subheader(
                    "Comparison Summary"
                )

                display_revision_summary(
                    comparison
                )

                st.divider()

                # ------------------------------------------------
                # DETAILS
                # ------------------------------------------------

                st.subheader(
                    "Detailed Architecture Changes"
                )

                changes = comparison.get(
                    "changes",
                    {}
                )

                titles = {
                    "components":
                        "Software Components",

                    "ports":
                        "Ports",

                    "interfaces":
                        "Interfaces",

                    "data_flows":
                        "Data Flows",

                    "dependencies":
                        "Dependencies",

                    "functional_flows":
                        "Functional Flows",

                    "architecture_relationships":
                        "Architecture Relationships"
                }

                for entity_type, result in (
                    changes.items()
                ):

                    summary = (
                        comparison
                        .get("summary", {})
                        .get(
                            entity_type,
                            {}
                        )
                    )

                    added_count = summary.get(
                        "added",
                        0
                    )

                    removed_count = summary.get(
                        "removed",
                        0
                    )

                    changed_count = summary.get(
                        "changed",
                        0
                    )

                    unchanged_count = summary.get(
                        "unchanged",
                        0
                    )

                    title = titles.get(
                        entity_type,
                        entity_type
                    )

                    with st.expander(
                        (
                            f"{title} "
                            f"(Added: {added_count}, "
                            f"Removed: {removed_count}, "
                            f"Changed: {changed_count})"
                        ),
                        expanded=(
                            added_count > 0
                            or removed_count > 0
                            or changed_count > 0
                        )
                    ):

                        st.caption(
                            f"Added: {added_count} | "
                            f"Removed: {removed_count} | "
                            f"Changed: {changed_count} | "
                            f"Unchanged: {unchanged_count}"
                        )

                        display_entity_changes(
                            entity_type,
                            result
                        )

                # ------------------------------------------------
                # DOWNLOAD
                # ------------------------------------------------

                st.divider()

                st.subheader(
                    "Export Comparison"
                )

                comparison_json = json.dumps(
                    comparison,
                    indent=2,
                    ensure_ascii=False
                )

                st.download_button(
                    label="Download Comparison JSON",
                    data=comparison_json,
                    file_name="revision_comparison.json",
                    mime="application/json"
                )

                # ------------------------------------------------
                # SAVE LOCALLY
                # ------------------------------------------------

                output_file = (
                    COMPARISON_DIRECTORY
                    / "revision_comparison_latest.json"
                )

                RevisionComparator.save_comparison(
                    output_file,
                    comparison
                )

                st.caption(
                    "Saved locally to: "
                    f"{output_file}"
                )

            except Exception as error:

                st.error(
                    "Unable to compare the revisions."
                )

                st.exception(
                    error
                )


# ============================================================
# 4. EVALUATION
# ============================================================

elif module == "Evaluation":

    st.header(
        "Architecture Evaluation"
    )

    st.write(
        "Evaluation results from the "
        "architecture extraction benchmark."
    )

    evaluation = load_evaluation()

    if not evaluation:

        st.warning(
            "Architecture evaluation results "
            "are not available."
        )

    else:

        entity_metrics = evaluation.get(
            "entity_metrics",
            {}
        )

        if entity_metrics:

            st.subheader(
                "Entity Metrics"
            )

            rows = []

            for entity_type, values in (
                entity_metrics.items()
            ):

                rows.append({
                    "Entity Type": entity_type,
                    "Precision": values.get(
                        "precision",
                        0
                    ),
                    "Recall": values.get(
                        "recall",
                        0
                    ),
                    "F1": values.get(
                        "f1",
                        0
                    )
                })

            st.dataframe(
                pd.DataFrame(rows),
                use_container_width=True,
                hide_index=True
            )

        macro_metrics = evaluation.get(
            "macro_metrics",
            {}
        )

        if macro_metrics:

            st.subheader(
                "Macro Metrics"
            )

            col1, col2, col3 = st.columns(3)

            with col1:

                st.metric(
                    "Precision",
                    f"{macro_metrics.get('precision', 0):.2%}"
                )

            with col2:

                st.metric(
                    "Recall",
                    f"{macro_metrics.get('recall', 0):.2%}"
                )

            with col3:

                st.metric(
                    "F1",
                    f"{macro_metrics.get('f1', 0):.2%}"
                )

        completeness = evaluation.get(
            "overall_completeness",
            evaluation.get(
                "completeness",
                None
            )
        )

        if completeness is not None:

            st.subheader(
                "Overall Completeness"
            )

            if isinstance(
                completeness,
                (float, int)
            ):

                if completeness <= 1:

                    value = completeness

                else:

                    value = completeness / 100

                st.metric(
                    "Completeness",
                    f"{value:.2%}"
                )

        consistency = evaluation.get(
            "consistency",
            {}
        )

        if consistency:

            st.subheader(
                "Consistency"
            )

            status = consistency.get(
                "status",
                "UNKNOWN"
            )

            if status == "PASS":

                st.success(
                    "Architecture consistency: PASS"
                )

            else:

                st.warning(
                    f"Architecture consistency: "
                    f"{status}"
                )

        with st.expander(
            "View Complete Evaluation JSON"
        ):

            st.json(
                evaluation
            )


# ============================================================
# 5. REPORTS
# ============================================================

elif module == "Reports":

    st.header(
        "Reports"
    )

    st.write(
        "Generated evaluation and retrieval reports."
    )

    report_files = [
        EVALUATION_FILE,
        RETRIEVAL_EVALUATION_FILE,
        RETRIEVAL_METRICS_FILE,
        ARCHITECTURE_METRICS_FILE
    ]

    found_reports = False

    for report in report_files:

        if not report.exists():
            continue

        found_reports = True

        st.subheader(
            report.name
        )

        if report.suffix.lower() == ".json":

            try:

                with open(
                    report,
                    "r",
                    encoding="utf-8"
                ) as file:

                    report_data = json.load(
                        file
                    )

                with st.expander(
                    "View report"
                ):

                    st.json(
                        report_data
                    )

            except Exception as error:

                st.warning(
                    f"Unable to read JSON: "
                    f"{error}"
                )

        elif report.suffix.lower() == ".csv":

            try:

                dataframe = pd.read_csv(
                    report
                )

                st.dataframe(
                    dataframe,
                    use_container_width=True,
                    hide_index=True
                )

            except Exception as error:

                st.warning(
                    f"Unable to display CSV: "
                    f"{error}"
                )

        with open(
            report,
            "rb"
        ) as file:

            st.download_button(
                label=f"Download {report.name}",
                data=file.read(),
                file_name=report.name,
                key=f"download_{report.name}"
            )

    if not found_reports:

        st.info(
            "No generated reports are currently available."
        )