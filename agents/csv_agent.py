from langchain_core.tools import StructuredTool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

from pipeline.data_manager import DataManager
from services.config import (
    AGENT_REQUEST_TIMEOUT_SECONDS,
    AGENT_RETRIES,
    AI_PROVIDER,
    GEMINI_MODEL,
    GOOGLE_API_KEY,
    GROQ_API_KEY,
    GROQ_MODEL,
)
from tools.data_tools import DataQuery, describe_data, query_data


def build_tools(data_manager: DataManager) -> list[StructuredTool]:
    query_tool = StructuredTool.from_function(
        func=lambda query: query_data(query, data_manager),
        name="query_data",
        description=(
            "Consulta dados carregados. Consulte describe_data antes, "
            "nunca invente datasets ou colunas e use count, list ou aggregate."
        ),
        args_schema=DataQuery,
    )
    describe_tool = StructuredTool.from_function(
        func=lambda: describe_data(data_manager),
        name="describe_data",
        description=(
            "Retorna datasets, número de registros, colunas, tipos e amostras. "
            "Use antes de query_data."
        ),
    )
    return [describe_tool, query_tool]


def create_agent(
    data_manager: DataManager | None = None,
    tools: list[StructuredTool] | None = None,
):
    """Cria o modelo com ferramentas ligadas ao DataManager da sessão."""
    api_key, model = _selected_credentials()
    if not api_key:
        raise RuntimeError(f"Chave não configurada para o provedor {AI_PROVIDER}")

    manager = data_manager or DataManager()
    bound_tools = tools or build_tools(manager)
    if AI_PROVIDER == "groq":
        llm = ChatGroq(
            model=model,
            temperature=0,
            api_key=api_key,
            timeout=AGENT_REQUEST_TIMEOUT_SECONDS,
            max_retries=AGENT_RETRIES,
        )
    else:
        llm = ChatGoogleGenerativeAI(
            model=model,
            temperature=0,
            google_api_key=api_key,
            request_timeout=AGENT_REQUEST_TIMEOUT_SECONDS,
            retries=AGENT_RETRIES,
            thinking_budget=0,
        )
    return llm.bind_tools(bound_tools)


def _selected_credentials() -> tuple[str | None, str]:
    if AI_PROVIDER == "groq":
        return GROQ_API_KEY, GROQ_MODEL
    return GOOGLE_API_KEY, GEMINI_MODEL
