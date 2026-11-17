
from pathlib import Path

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma


# Locate the project folder
BASE_PATH = Path(__file__).resolve().parents[2]
CHROMA_PATH = BASE_PATH / "Chroma"


def mapping_agent(profile):

    print("MAPPING AGENT IS RUNNING!")

    # 1. Get information from the user's AI system profile
    system_name = profile.get("system_name", "Not provided")
    scenario = profile.get("scenario_description", "Not provided")
    industry = profile.get("industry", "Not provided")
    model_type = profile.get("model_type", "Not provided")

    print("System:", system_name)

    # 2. Prepare a search query
    query = f"""
    AI system: {system_name}
    Scenario: {scenario}
    Industry: {industry}
    AI model type: {model_type}

    Identify relevant cybersecurity and AI governance
    framework controls, including data protection,
    privacy, access control, authentication,
    third-party security and AI system risks.
    """

    # 3. Load the same embedding model used during ingestion
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    # 4. Connect to the existing Chroma database
    vector_store = Chroma(
        collection_name="cybersecurity_knowledge",
        embedding_function=embeddings,
        persist_directory=str(CHROMA_PATH)
    )

    # 5. Check whether the database contains documents
    total_records = vector_store._collection.count()

    if total_records == 0:
        return {
            "mapping_status": "NO_DATA",
            "mapped_controls": [],
            "source_verified": False,
            "mapping_message": "ChromaDB contains no documents. Please ingest framework PDFs first."
        }

    # 6. Retrieve the 5 most relevant document chunks
    results = vector_store.similarity_search(
        query,
        k=min(5, total_records)
    )

     # 7. Prepare retrieved results
    mapped_controls = []

    for document in results:

        metadata = document.metadata

        # Display retrieved document information in terminal
        print("\nRETRIEVED DOCUMENT:")
        print("Source:", metadata.get("source"))
        print("Page:", metadata.get("page"))
        print("Content:", document.page_content[:300])
        print("-----------------------------")

        # Store retrieved information
        mapped_controls.append({
            "control": metadata.get("control_id", "Not identified"),
            "framework": metadata.get("framework", "Not specified"),
            "description": document.page_content,
            "source": metadata.get("source", "Unknown source"),
            "page": (
                int(metadata["page"]) + 1
                if metadata.get("page") is not None
                else "Unknown page"
            )
        })


    # 8. Return mapping results
    print("Retrieved controls:", len(mapped_controls))

    return {
        "mapping_status": "COMPLETED",
        "mapped_controls": mapped_controls,
        "source_verified": False,
        "mapping_message": (
            f"Retrieved {len(mapped_controls)} relevant document chunks "
            "from ChromaDB. Source details are available for review."
        )
    }

