from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os

load_dotenv()

def get_llm():
    groq_key = os.getenv("GROQ_API_KEY")
    
    if not groq_key:
        raise ValueError("GROQ_API_KEY not found in environment variable")
    else:
        return ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=groq_key,
            temperature=0.2,
        )