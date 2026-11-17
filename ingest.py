from pathlib import Path
import re

from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma


# 1. Locate project folders
BASE_PATH = Path(__file__).resolve().parent
PDF_PATH = BASE_PATH / "PDF"
CHROMA_PATH = BASE_PATH / "Chroma"

print("PDF folder:", PDF_PATH)
print("Chroma folder:", CHROMA_PATH)


# 2. Identify framework using PDF filename
def identify_document(source):

    filename = Path(source).name.lower()

    if "ai verify" in filename:
        return "AI Verify"

    elif "feat" in filename:
        return "FEAT Principles"

    elif "23894" in filename:
        return "ISO/IEC 23894:2023"

    elif "42001" in filename:
        return "ISO/IEC 42001:2023"

    elif "mitre atlas" in filename:
        return "MITRE ATLAS (Secondary Article)"

    elif "model-ai-governance" in filename:
        return "Singapore Model AI Governance Framework for Generative AI"

    elif "nist" in filename:
        return "NIST AI RMF 1.0"

    elif "owasp" in filename:
        return "OWASP Top 10 for LLM Applications 2025"

    else:
        return "Unclassified"


# 3. Load all PDF files
pdf_files = list(PDF_PATH.glob("*.pdf"))

print("\nPDF documents found:", len(pdf_files))

for pdf in pdf_files:
    print("-", pdf.name)

if not pdf_files:
    raise ValueError("No PDF files found in the PDF folder.")


loader = PyPDFDirectoryLoader(str(PDF_PATH))
documents = loader.load()

print("\nPDF pages loaded:", len(documents))


# 4. Split PDF text into chunks
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)

chunks = text_splitter.split_documents(documents)

print("Text chunks created:", len(chunks))


# 5. Extract identifiable framework references
def extract_references(text, framework):

    patterns = {
        "OWASP Top 10 for LLM Applications 2025":
            r"\bLLM\d{2}(?::2025)?\b",

        "NIST AI RMF 1.0":
            r"\b(?:GOVERN|MAP|MEASURE|MANAGE)\s+\d+\.\d+\b",

        "ISO/IEC 23894:2023":
            r"\b\d+(?:\.\d+){1,3}\b",

        "ISO/IEC 42001:2023":
            r"\b\d+(?:\.\d+){1,3}\b",

        "FEAT Principles":
            r"\b(?:F|E|A|T)\d+(?:\.\d+)*\b"
    }

    pattern = patterns.get(framework)

    if not pattern:
        return []

    matches = re.findall(pattern, text, flags=re.IGNORECASE)

    return list(dict.fromkeys(matches))


# 6. Add metadata to each chunk
for chunk in chunks:

    source = chunk.metadata.get("source", "Unknown source")

    framework = identify_document(source)

    references = extract_references(
        chunk.page_content,
        framework
    )

    chunk.metadata["framework"] = framework
    chunk.metadata["document_name"] = Path(source).name
    chunk.metadata["reference_ids"] = ", ".join(references)
    chunk.metadata["reference_type"] = (
        "Detected reference" if references else "Not identified"
    )

print("\nMetadata added to chunks.")

# 7. Load embedding model
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


# 8. Create ChromaDB
vector_store = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    collection_name="cybersecurity_knowledge",
    persist_directory=str(CHROMA_PATH)
)


# 9. Confirm database
print("\nIngestion completed successfully!")
print("Total records:", vector_store._collection.count())

print("\nFramework summary:")

frameworks = {}

for chunk in chunks:
    framework = chunk.metadata["framework"]
    frameworks[framework] = frameworks.get(framework, 0) + 1

for framework, count in frameworks.items():
    print(f"{framework}: {count} chunks")
