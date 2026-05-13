from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

load_dotenv()

def get_llm(provider=None, model=None, temperature=0.2):
    provider = provider or os.getenv("LLM_PROVIDER", "groq").lower()
    
    # Try OpenAI if requested
    if provider == "openai":
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            model_name = model or os.getenv("LLM_MODEL", "gpt-4o-mini")
            return ChatOpenAI(
                model=model_name,
                api_key=openai_key,
                temperature=temperature,
            )
        else:
            # Fallback to Groq if OpenAI is requested but no key is available
            print("⚠️ OPENAI_API_KEY not found. Falling back to Groq.")
            provider = "groq"
            
    # Default to Groq
    if provider == "groq":
        groq_key = os.getenv("GROQ_API_KEY")
        if not groq_key:
            raise ValueError("GROQ_API_KEY not found in environment variable")
        
        model_name = model or os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
        return ChatGroq(
            model=model_name,
            api_key=groq_key,
            temperature=temperature,
        )
        
    raise ValueError(f"Unsupported LLM provider: {provider}")