from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
 
CHROMA_PATH = r"Z:\FYP\Chroma"
 
# Load the same embedding model used during ingestion
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)
 
# Connect to the existing ChromaDB database
vector_store = Chroma(
    collection_name="cybersecurity_knowledge",
    embedding_function=embeddings,
    persist_directory=CHROMA_PATH
)
 
print("Total records:", vector_store._collection.count())
 
# Ask a test question
question = input("Enter your question: ")
 
# Retrieve the 3 most relevant text chunks
results = vector_store.similarity_search(
    question,
    k=3
)
 
print("\nRetrieved information:\n")
 
for document in results:
    print("Source:", document.metadata)
    print(document.page_content)
    print("--------------------------------")    