"""
Google Gemini API wrapper.
Uses gemini-1.5-flash for fast, cost-effective responses.
Lazy-imports google.generativeai so the app starts without the package installed.
"""
from app.config import get_settings
from app.utils.logger import get_logger
from app.utils.exceptions import ExternalServiceError

logger = get_logger(__name__)
settings = get_settings()

_model = None


def _get_model():
    global _model
    if _model is None:
        try:
            import google.generativeai as genai  # lazy import
        except ImportError:
            raise ExternalServiceError(
                "Gemini",
                "google-generativeai package not installed. Run: pip install google-generativeai",
            )
        if not settings.gemini_api_key:
            raise ExternalServiceError("Gemini", "GEMINI_API_KEY is not configured")

        genai.configure(api_key=settings.gemini_api_key)
        _model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=(
                "You are an expert software architect and code intelligence assistant "
                "for the Living Architecture Map platform. You help developers understand "
                "their codebase structure, dependencies, and architecture. "
                "Be concise, technical, and accurate. Use bullet points where appropriate."
            ),
        )
    return _model


async def ask_gemini(context: str, question: str) -> str:
    """
    Send a question with architecture context to Gemini and return the response.
    """
    try:
        model = _get_model()
        prompt = f"{context}\n\n## Developer Question\n{question}"
        response = await model.generate_content_async(prompt)
        return response.text
    except ExternalServiceError:
        raise
    except Exception as e:
        logger.error("Gemini API call failed", error=str(e))
        raise ExternalServiceError("Gemini", str(e))
