from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
 
PDF_PATH = r"Z:\FYP\PDF"
CHROMA_PATH = r"Z:\FYP\Chroma"
 
# Step 1: Load all PDF files
loader = PyPDFDirectoryLoader(PDF_PATH)
documents = loader.load()
 
print("PDF pages loaded:", len(documents))
 
# Step 2: Split the extracted text into smaller chunks
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)
 
chunks = text_splitter.split_documents(documents)
 
print("Text chunks created:", len(chunks))
 
# Step 3: Load the embedding model
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)
 
# Step 4: Store the chunks and embeddings in ChromaDB
vector_store = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    collection_name="cybersecurity_knowledge",
    persist_directory=CHROMA_PATH
)
 
print("Documents stored successfully!")
print("Total records:", vector_store._collection.count())