from pathlib import Path

import fitz


class PDFLoader:
    """
    Loads PDF documents from disk.

    Responsibilities:
        • Discover PDF files
        • Extract text page-by-page
        • Preserve page numbers
        • Attach document metadata
    """

    def __init__(self, documents_path):

        project_root = Path(__file__).resolve().parents[2]

        self.documents_path = project_root / documents_path

    def load(self) -> list[dict]:
        """
        Returns a list of pages.

        Example:

        [
            {
                "text": "...",
                "source": "KPI_Definitions.pdf",
                "page": 1,
                "document_type": "company",
                "metadata": {...}
            }
        ]
        """

        pages = []

        for pdf_path in sorted(self.documents_path.rglob("*.pdf")):

            pages.extend(self._load_pdf(pdf_path))

        return pages

    def _load_pdf(
        self,
        pdf_path: Path,
    ) -> list[dict]:

        document = fitz.open(pdf_path)

        document_type = self._document_type(pdf_path)

        pages = []

        for page_number in range(len(document)):

            page = document.load_page(page_number)

            text = page.get_text("text").strip()

            if not text:
                continue

            pages.append(
                {
                    "text": text,
                    "source": pdf_path.name,
                    "page": page_number + 1,
                    "document_type": document_type,
                    "metadata": {
                        "source": pdf_path.name,
                        "page": page_number + 1,
                        "document_type": document_type,
                    },
                }
            )

        document.close()

        return pages

    @staticmethod
    def _document_type(
        pdf_path: Path,
    ) -> str:
        """
        Classify documents based on folder.

        data/use_case_docs/company/*.pdf
            -> company

        data/use_case_docs/standards/*.pdf
            -> standards
        """

        parts = [part.lower() for part in pdf_path.parts]

        if "company" in parts:
            return "company"

        if "standards" in parts:
            return "standards"

        return "unknown"
