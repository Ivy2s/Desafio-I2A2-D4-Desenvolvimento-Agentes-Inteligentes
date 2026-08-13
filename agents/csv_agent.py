from langchain_google_genai import ChatGoogleGenerativeAI

from services.config import GOOGLE_API_KEY
from agents.prompts import SYSTEM_PROMPT


def create_agent():
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        google_api_key=GOOGLE_API_KEY,
    )

    return llm