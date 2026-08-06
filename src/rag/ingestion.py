from rag.document_loader import PDFLoader
from rag.splitter import DocumentSplitter
from rag.vector_store import VectorStore

DOCUMENTS_PATH = "data/use_case_docs"


def main() -> None:

    print("=" * 60)
    print("ESG Knowledge Base Ingestion")
    print("=" * 60)

    loader = PDFLoader(DOCUMENTS_PATH)

    pages = loader.load()

    print(f"Loaded {len(pages)} pages")

    splitter = DocumentSplitter()

    chunks = splitter.split(pages)

    print(f"Generated {len(chunks)} chunks")

    vector_store = VectorStore()

    print(f"Existing vectors: {vector_store.count()}")

    vector_store.add_documents(chunks)

    print(f"Vectors after ingestion: {vector_store.count()}")

    print("Knowledge base created successfully.")


if __name__ == "__main__":
    main()
