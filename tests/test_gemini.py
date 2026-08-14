from langchain_google_genai import ChatGoogleGenerativeAI
from services.config import GOOGLE_API_KEY

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    google_api_key=GOOGLE_API_KEY,
)

response = llm.invoke(
    "Explique em uma frase o que é uma nota fiscal."
)

print(response.content)