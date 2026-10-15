# AUTOSAR HLD Document Analysis Assistant

An evidence-grounded architecture analysis assistant for extracting, organizing, searching, validating, and comparing architectural knowledge from AUTOSAR High-Level Design (HLD) documents.

This project was developed as a practical implementation of the **Tata Techpulse Automotive Engineering AI case study**.

---

## 1. Project Overview

AUTOSAR High-Level Design documents describe software components, ports, interfaces, signals, data flows, dependencies, functional flows, and relationships between architectural elements.

Finding specific information and comparing revisions manually can be time-consuming for automotive software engineers.

The AUTOSAR HLD Document Analysis Assistant processes HLD PDFs into structured architecture knowledge and provides a searchable interface for asking architecture-related questions. It retrieves supporting evidence and provides document, page, and section references wherever available.

The system also supports architecture revision comparison, citation validation, and evaluation of extraction and retrieval quality.

The current implementation uses a synthetic demonstration HLD document. Its results should be validated against real AUTOSAR documents before production use.

## 2. Project Objectives

The primary objectives are to:

1. Extract architectural information from HLD PDF documents.
2. Organize extracted information into structured records.
3. Build searchable architecture knowledge.
4. Support natural-language architecture queries.
5. Retrieve relevant evidence using semantic and structured search.
6. Generate evidence-grounded answers.
7. Preserve document, page, and section traceability.
8. Validate answer citations against retrieved evidence.
9. Compare two architecture revisions.
10. Evaluate extraction, retrieval, completeness, and consistency.
11. Provide a Streamlit user interface and FastAPI REST API.

## 3. System Architecture

```text
                AUTOSAR HLD PDF
                       |
                       v
                PDF Ingestion
                  (PyMuPDF)
                       |
                       v
              Text and Page Extraction
                       |
                       v
            Architecture Information
                  Extraction
                       |
                       v
           Structured Architecture JSON
                       |
                       v
              Architecture Chunking
                       |
                       v
                FastEmbed Model
                       |
                       v
                 FAISS Index
                       |
                       v
                Hybrid Retrieval
                /             \
               v               v
       Semantic Search    Structured Search
                \             /
                 v           v
                Evidence Selection
                       |
                       v
                Answer Generation
                       |
                       v
                Citation Validation
                       |
                       v
               Evidence-Grounded Answer
```

The application also includes separate workflows for architecture revision comparison, evaluation, report generation, and query-history tracking.

## 4. Key Features

### 4.1 PDF Ingestion

- Reads PDF documents using PyMuPDF.
- Extracts text at page level.
- Preserves available document and page metadata.
- Supports identification of pages with insufficient extracted text for further OCR investigation.

### 4.2 Architecture Extraction

Extracts structured architecture information, including:

- Software components
- Ports
- Interfaces
- Data flows
- Dependencies
- Functional flows
- Architecture relationships

Extracted records can retain source document, page number, section number, and section title information where available.

**Implementation note:** The current extraction implementation uses pattern-based rules and assumptions about document structure. Its extraction quality depends on the document's formatting and terminology.

### 4.3 Architecture Knowledge Base

- Stores extracted architecture entities as structured JSON.
- Converts architecture information into searchable chunks.
- Maintains metadata for evidence traceability.
- Supports structured and semantic representations of architecture knowledge.

### 4.4 Hybrid Retrieval

The retrieval workflow combines:

- Semantic search using FastEmbed embeddings and FAISS.
- Structured search over architecture metadata.
- Query-intent handling.
- Evidence deduplication.
- Query-specific evidence filtering.

The goal is to retrieve useful architectural evidence while preserving its source information.

### 4.5 Evidence-Grounded Question Answering

Users can ask natural-language questions about the architecture.

The answer-generation layer produces responses using retrieved evidence. Answers can include citations in the following format:

`Document | Page | Section`

The current demonstration supports deterministic, evidence-grounded answer generation without requiring an external LLM API for its core question-answering workflow.

### 4.6 Citation Validation

The citation-validation module checks whether citations in generated answers are supported by the retrieved evidence.

Citation coverage measures citation presence or support according to the project's evaluation procedure. It should not be interpreted as proof that every generated statement is factually correct.

### 4.7 Architecture Revision Comparison

The system compares two architecture revisions to identify:

- Added entities
- Removed entities
- Changed entities
- Unchanged entities

Comparison supports the architecture entity categories implemented in the project, including components, ports, interfaces, data flows, dependencies, functional flows, and architecture relationships.

### 4.8 Evaluation and Reports

The project includes evaluation workflows and notebooks for:

- Retrieval evaluation
- Architecture extraction evaluation
- Precision, recall, and F1-score
- Completeness analysis
- Citation coverage
- Dataset exploration
- Architecture consistency checks
- Feature engineering
- Retrieval configuration experiments

## 5. Technology Stack

| Layer | Technology |
|---|---|
| Programming language | Python |
| PDF processing | PyMuPDF |
| Data processing | NumPy, Pandas |
| Embeddings | FastEmbed |
| Embedding model | BAAI/bge-small-en-v1.5 |
| Vector search | FAISS |
| Web interface | Streamlit |
| REST API | FastAPI |
| API server | Uvicorn |
| Database | SQLite |
| LLM integration | Optional OpenAI API interface |
| Experimentation | Jupyter Notebook, JupyterLab |
| Development | Visual Studio Code |
| Version control | Git, GitHub |

## 6. Project Structure

```text
autosar_hld_assistant/
â”œâ”€â”€ api/
â”‚   â””â”€â”€ main.py
â”œâ”€â”€ app/
â”‚   â””â”€â”€ streamlit_app.py
â”œâ”€â”€ data/
â”‚   â”œâ”€â”€ hld_documents/
â”‚   â”‚   â””â”€â”€ sample_autosar_hld.pdf
â”‚   â””â”€â”€ processed/
â”œâ”€â”€ database/
â”‚   â””â”€â”€ database.py
â”œâ”€â”€ eval/
â”‚   â””â”€â”€ results/
â”œâ”€â”€ notebooks/
â”‚   â”œâ”€â”€ 01_hld_ingestion.ipynb
â”‚   â”œâ”€â”€ 02_architecture_extraction.ipynb
â”‚   â”œâ”€â”€ 03_autosar_rag_assistant.ipynb
â”‚   â”œâ”€â”€ 04_retrieval_eval_prompts.ipynb
â”‚   â”œâ”€â”€ 05_architecture_evaluation.ipynb
â”‚   â”œâ”€â”€ 06_dataset_eda.ipynb
â”‚   â”œâ”€â”€ 07_retrieval_experiments.ipynb
â”‚   â””â”€â”€ 08_feature_engineering_retrieval_optimization.ipynb
â”œâ”€â”€ outputs/
â”‚   â”œâ”€â”€ comparison/
â”‚   â”œâ”€â”€ evaluation/
â”‚   â”œâ”€â”€ extracted_entities/
â”‚   â”œâ”€â”€ rag_index/
â”‚   â”œâ”€â”€ reports/
â”‚   â””â”€â”€ structured_export/
â”œâ”€â”€ src/
â”‚   â”œâ”€â”€ ingestion/
â”‚   â”œâ”€â”€ extraction/
â”‚   â”œâ”€â”€ chunking/
â”‚   â”œâ”€â”€ embeddings/
â”‚   â”œâ”€â”€ retrieval/
â”‚   â”œâ”€â”€ generation/
â”‚   â”œâ”€â”€ guardrails/
â”‚   â”œâ”€â”€ comparison/
â”‚   â””â”€â”€ evaluation/
â”œâ”€â”€ .dockerignore
â”œâ”€â”€ .gitignore
â”œâ”€â”€ Dockerfile
â”œâ”€â”€ docker-compose.yml
â”œâ”€â”€ README.md
â””â”€â”€ requirements.txt
```

Additional generated files and Python modules may exist in the repository. The tree above highlights the primary application and experiment directories.

## 7. Evaluation Results

The current demonstration uses a synthetic AUTOSAR HLD document. Results are based on small, project-specific evaluation sets and are not production benchmarks.

### 7.1 Retrieval Evaluation

An earlier retrieval evaluation reported the following results:

| Metric | Reported result |
|---|---:|
| Retrieval accuracy | 100% |
| Top-1 accuracy | 60% |
| Top-3 accuracy | 100% |
| Top-5 accuracy | 100% |
| Top-10 accuracy | 100% |
| Mean precision | 92% |
| Mean recall | 100% |
| Mean F1-score | 95.56% |
| Citation coverage | 100% |
| Query-type accuracy | 100% |

These figures belong to the earlier evaluation workflow and its test definitions. They should not be assumed to measure the same thing as the later retrieval optimization experiment.

### 7.2 Architecture Extraction Evaluation

The earlier architecture evaluation reported:

| Entity type | Precision | Recall | F1-score |
|---|---:|---:|---:|
| Components | 100% | 100% | 100% |
| Ports | 100% | 100% | 100% |
| Interfaces | 100% | 100% | 100% |
| Data flows | 100% | 80% | 88.89% |
| Dependencies | 100% | 100% | 100% |
| Functional flows | 100% | 100% | 100% |
| Architecture relationships | 100% | 100% | 100% |

**Reported overall completeness: 97.14%.**

The results reflect the project's demonstration data and provisional evaluation labels. They do not establish equivalent performance on unseen documents or large production datasets.

### 7.3 Retrieval Optimization Experiment

Notebook 08 compared semantic, structured, and hybrid retrieval across five test queries using different `top_k` settings.

The selected configuration was **hybrid retrieval with `top_k = 3`**, which achieved 100% mean expected-term coverage across the five test queries in that experiment.

Expected-term coverage measures how many predefined expected terms are present in retrieved results. It is not the same as standard retrieval accuracy, semantic relevance, or answer correctness.

The small test set is useful for comparing configurations during development, but larger and independently labelled datasets are needed for reliable generalization claims.

## 8. Installation and Setup

### Prerequisites

- Python 3.12 recommended for the documented environment.
- Git.
- Visual Studio Code or another Python development environment.
- Internet access for installing dependencies and downloading the embedding model when it is not already cached.

### Step 1: Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd autosar_hld_assistant
```

Replace the placeholder with your actual GitHub repository URL.

If you already have the project locally, open its root directory instead.

### Step 2: Create a virtual environment

**Windows PowerShell**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux or macOS**

```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Dependency installation may take some time because the project includes machine-learning and vector-search libraries.

### Step 4: Verify the sample data

Confirm that the demonstration PDF exists:

```text
data/hld_documents/sample_autosar_hld.pdf
```

The application also uses the project's processed architecture knowledge and retrieval artifacts where required by the implementation.

## 9. Running the Application

Run the commands from the project root with the virtual environment activated.

### Terminal 1: Start the FastAPI backend

```bash
python -m uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

Open:

- API health endpoint: `http://127.0.0.1:8000/health`
- Interactive API documentation: `http://127.0.0.1:8000/docs`

### Terminal 2: Start the Streamlit interface

Activate the virtual environment in the second terminal, then run:

```bash
python -m streamlit run app/streamlit_app.py
```

Open the local URL printed in the terminal, normally:

`http://localhost:8501`

The interface includes the implemented workflows for architecture overview, question answering, revision comparison, evaluation, and reports.

## 10. REST API Endpoints

The FastAPI application implements the following routes:

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Root endpoint |
| GET | `/health` | Health check |
| GET | `/architecture` | Architecture information |
| POST | `/query` | Submit an architecture question |
| POST | `/compare` | Compare architecture revisions |
| GET | `/query-history` | Query history |
| GET | `/comparison-history` | Comparison history |
| GET | `/documents` | Document information |

Request fields and response schemas are defined in `api/main.py`. Refer to `/docs` after starting the backend for the actual schemas and available operations.

## 11. Configuration and API Keys

The core demonstration workflow uses deterministic answer generation and does not require an OpenAI API key for that workflow.

If an optional LLM integration is enabled, configure its credentials through environment variables as required by the implementation.

Keep credentials in a local `.env` file when applicable. Never commit `.env`, API keys, passwords, or other secrets to GitHub.

## 12. Current Limitations

- **Synthetic evaluation data:** The current results are based on a small demonstration HLD dataset.
- **Pattern-based extraction:** Unfamiliar document layouts and terminology may require changes to extraction rules.
- **Scanned PDFs:** Pages that contain images rather than extractable text may require an OCR pipeline.
- **Evaluation coverage:** Larger and independently labelled datasets are needed to assess generalization.
- **Revision matching:** Comparison quality depends on entity extraction, identifiers, and matching logic.
- **Answer grounding:** Citation validation helps check evidence traceability but cannot guarantee that every statement is correct.
- **Production readiness:** Real-world deployment would require additional validation, security controls, performance testing, and handling of diverse AUTOSAR document formats.

## 13. Future Enhancements

Potential extensions include:

1. Integrating OCR for scanned HLD documents.
2. Improving architecture extraction with schema validation and domain-specific models.
3. Supporting larger collections of real AUTOSAR HLD documents.
4. Evaluating retrieval with larger, independently labelled query sets.
5. Improving entity resolution across document revisions.
6. Adding richer architecture dependency visualizations.
7. Strengthening citation validation and unsupported-answer detection.
8. Adding access control, monitoring, and production deployment configuration.

## 14. Conclusion

The AUTOSAR HLD Document Analysis Assistant demonstrates a workflow for converting architectural information from HLD PDFs into structured, searchable knowledge.

By combining document processing, architecture extraction, hybrid retrieval, evidence-grounded question answering, citation validation, and revision comparison, the project provides a foundation for assisting automotive software engineers with architecture analysis.

The implementation and evaluation notebooks document the current approach and its experimental results. Further validation on real-world AUTOSAR documents is necessary before drawing production-level conclusions.

---

**Project:** AUTOSAR HLD Document Analysis Assistant
**Use case:** Tata Techpulse Automotive Engineering AI case study
**Primary technologies:** Python, FastAPI, Streamlit, PyMuPDF, FastEmbed, FAISS
