from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

from utils.retry import with_retry

load_dotenv()


class _RetryableLLM:
    """
    Thin proxy around a LangChain LLM instance.

    Why a proxy instead of monkey-patching?
    ChatGroq / ChatOpenAI are Pydantic v2 models. Pydantic v2 forbids
    setting arbitrary attributes on model instances, so:
        llm.invoke = wrapped_fn   →   ValueError: no field "invoke"

    This wrapper owns a *retried* version of invoke and forwards every
    other attribute access transparently to the underlying model, so the
    rest of the LangChain / LangGraph machinery (streaming, bind, etc.)
    keeps working without changes.
    """

    def __init__(self, llm, max_attempts: int, base_delay: float, max_delay: float):
        # Store on object's own __dict__ to bypass any __setattr__ magic
        object.__setattr__(self, "_llm", llm)
        object.__setattr__(
            self,
            "invoke",
            with_retry(
                max_attempts=max_attempts,
                base_delay=base_delay,
                max_delay=max_delay,
            )(llm.invoke),
        )

    def __getattr__(self, name: str):
        # Delegate anything we don't own to the real LLM
        return getattr(object.__getattribute__(self, "_llm"), name)


def _apply_retry(llm) -> _RetryableLLM:
    """
    Wrap *llm* in a retry-aware proxy.  All agents that call get_llm()
    automatically get exponential-backoff coverage — no per-agent changes
    needed.
    """
    return _RetryableLLM(
        llm,
        max_attempts=int(os.getenv("NODEGUARD_RETRY_MAX_ATTEMPTS", "5")),
        base_delay=float(os.getenv("NODEGUARD_RETRY_BASE_DELAY", "1.0")),
        max_delay=float(os.getenv("NODEGUARD_RETRY_MAX_DELAY", "60.0")),
    )


def get_llm(provider=None, model=None, temperature=0.2):
    provider = provider or os.getenv("LLM_PROVIDER", "groq").lower()

    # Try OpenAI if requested
    if provider == "openai":
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            model_name = model or os.getenv("LLM_MODEL", "gpt-4o-mini")
            llm = ChatOpenAI(
                model=model_name,
                api_key=openai_key,
                temperature=temperature,
            )
            return _apply_retry(llm)
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
        llm = ChatGroq(
            model=model_name,
            api_key=groq_key,
            temperature=temperature,
        )
        return _apply_retry(llm)

    raise ValueError(f"Unsupported LLM provider: {provider}")