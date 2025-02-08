from langchain_openai import OpenAIEmbeddings
from langchain_groq import ChatGroq
from config import OPENAI_API_KEY
from db import get_user_groq_api_key
from langchain_nomic import NomicEmbeddings
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Load environment variables from .env file if it exists
load_dotenv
def create_embeddings():
    # OPENAI_API_KEY = "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"
    return NomicEmbeddings(
    model="nomic-embed-text-v1.5",
    # api_key="nk-W3huYcOUS_-GztrGv509-7MxCl8u1GIBRy8hZASQuX0"
  
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
