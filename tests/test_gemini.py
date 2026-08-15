from langchain_google_genai import ChatGoogleGenerativeAI
from services.config import GOOGLE_API_KEY


def main():
    if not GOOGLE_API_KEY:
        raise RuntimeError("Defina GOOGLE_API_KEY para executar este smoke test")
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        google_api_key=GOOGLE_API_KEY,
    )
    response = llm.invoke("Explique em uma frase o que é uma nota fiscal.")
    print(response.content)


if __name__ == "__main__":
    main()
