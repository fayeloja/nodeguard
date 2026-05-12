from langchain_openai import ChatOpenAI
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
        return ChatOpenAI(
            model="llama-3.3-70b-versatile",
            openai_api_key=os.getenv("GROQ_API_KEY"),
            openai_api_base="https://api.groq.com/openai/v1",
            temperature=0.2,
        )