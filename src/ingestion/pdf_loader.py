# src/ingestion/pdf_loader.py

from pathlib import Path
import json
import pymupdf


class PDFLoader:
    """
    Loads AUTOSAR HLD PDF documents and extracts
    page-level text and metadata.
    """

    def __init__(self, pdf_path):
        self.pdf_path = Path(pdf_path)

        if not self.pdf_path.exists():
            raise FileNotFoundError(
                f"PDF not found: {self.pdf_path}"
            )

        if self.pdf_path.suffix.lower() != ".pdf":
            raise ValueError(
                "PDFLoader only supports PDF files."
            )

    def load(self):
        """
        Extract page-level text from the PDF.
        """

        document = pymupdf.open(
            self.pdf_path
        )

        pages = []

        for page_number, page in enumerate(
            document,
            start=1
        ):

            text = page.get_text("text")

            pages.append({
                "page": page_number,
                "text": text.strip(),
                "character_count": len(
                    text.strip()
                ),
                "needs_ocr": (
                    len(text.strip()) < 50
                )
            })

        metadata = {
            "document": self.pdf_path.name,
            "path": str(
                self.pdf_path
            ),
            "total_pages": len(document)
        }

        document.close()

        return {
            "metadata": metadata,
            "pages": pages
        }

    def save(
        self,
        output_path,
        data=None
    ):
        """
        Save extracted PDF data as JSON.
        """

        if data is None:
            data = self.load()

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
                data,
                file,
                indent=2,
                ensure_ascii=False
            )

        return output_path