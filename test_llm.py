
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load API settings from .env
load_dotenv()

# Connect to Llama 4 Scout
llm = ChatOpenAI(
    model=os.getenv("LLAMA_MODEL"),
    base_url=os.getenv("LLAMA_BASE_URL"),
    api_key=os.getenv("LLAMA_API_KEY"),
    temperature=0
)

# Send a test prompt
response = llm.invoke(
    "You are an AI security assistant. "
    "Briefly introduce yourself and explain how you can help assess AI security risks."
)

print("\nLLM RESPONSE:")
print(response.content)
