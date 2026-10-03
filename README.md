# AUTOSAR HLD Document Analysis Assistant

An AI-assisted architecture analysis system for extracting, searching, validating, and comparing architectural knowledge from AUTOSAR High-Level Design (HLD) documents.

The project was developed as a practical implementation of the Tata Techpulse Automotive Engineering AI case study.

---

## 1. Project Overview

AUTOSAR High-Level Design documents can contain hundreds of pages describing:

- Software components
- Ports
- Interfaces
- Signals
- Data flows
- Dependencies
- Functional flows
- Architecture relationships
- Revision information

Manually searching and comparing this information can require significant engineering effort.

This project provides an evidence-grounded assistant that converts extracted HLD architecture information into a searchable knowledge base and provides traceable answers with document, page, and section citations.

The system also supports architecture revision comparison and evaluation.

---

## 2. Objectives

The main objectives are:

1. Extract architectural information from HLD documents.
2. Organize architecture information into structured records.
3. Create searchable architecture knowledge.
4. Support natural-language architecture questions.
5. Retrieve relevant architecture evidence.
6. Generate answers grounded in retrieved evidence.
7. Provide page and section citations.
8. Validate citation coverage.
9. Compare different architecture revisions.
10. Evaluate extraction and retrieval quality.
11. Provide both a Streamlit interface and REST API.

---

## 3. System Architecture

```text
                    AUTOSAR HLD PDF
                           |
                           v
                  +------------------+
                  |   PDF Ingestion  |
                  +------------------+
                           |
                           v
                  +------------------+
                  | Architecture     |
                  | Extraction       |
                  +------------------+
                           |
                           v
              Architecture Knowledge JSON
                           |
                           v
                  +------------------+
                  | Architecture     |
                  | Chunking         |
                  +------------------+
                           |
                           v
                  +------------------+
                  | FastEmbed        |
                  | Embeddings       |
                  +------------------+
                           |
                           v
                  +------------------+
                  | FAISS Vector     |
                  | Index            |
                  +------------------+
                           |
                           v
                    Hybrid Retrieval
                    /              \
                   /                \
        Semantic Search       Structured Search
                   \                /
                    \              /
                     v            v
                       Evidence
                           |
                           v
                  +------------------+
                  | Answer Generator |
                  +------------------+
                           |
                           v
                  Citation Validation
                           |
                           v
                    Final Answer