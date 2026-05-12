from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os

load_dotenv()

def get_llm():
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if openai_key:
        return ChatOpenAI(
            model="gpt-4o",
            temperature=0.2,
        )
    else:
        return ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=os.getenv("GROQ_API_KEY"),
            temperature=0.2,
        )