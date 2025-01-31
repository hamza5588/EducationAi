from langchain_openai import OpenAIEmbeddings
from langchain_groq import ChatGroq
from config import OPENAI_API_KEY
from db import get_user_groq_api_key

def create_embeddings():
    return OpenAIEmbeddings(
        api_key=OPENAI_API_KEY,
        model="text-embedding-3-small"
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