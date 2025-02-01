from langchain_openai import OpenAIEmbeddings
from langchain_groq import ChatGroq
from db import get_user_groq_api_key
from langchain_nomic import NomicEmbeddings
def create_embeddings():
    apikey = "nk-cKoV2oTQZO0sOH90NzNn5FXxqPULCO04srGOI9sXo5M"
    return embeddings = NomicEmbeddings(
    model="nomic-embed-text-v1.5",
    api_key=apikey,
  
)
embeddings = create_embeddings()

def get_chat_model(user_id):
    """Create a chat model instance with the user's API key"""
    api_key = get_user_groq_api_key(user_id)
    if not api_key:
        raise ValueError("No API key found for user")
    
    return ChatGroq(
        api_key=api_key,
        model_name="llama-3.1-8b-instant"
    )
