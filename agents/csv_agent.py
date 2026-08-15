from langchain_core.tools import StructuredTool
from langchain_google_genai import ChatGoogleGenerativeAI

from pipeline.data_manager import DataManager
from services.config import (
    AGENT_REQUEST_TIMEOUT_SECONDS,
    AGENT_RETRIES,
    GEMINI_MODEL,
    GEMINI_MODEL_ALT,
    GEMINI_PROFILE,
    GOOGLE_API_KEY,
    GOOGLE_API_KEY_ALT,
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
    google_api_key, gemini_model = _selected_credentials()
    if not google_api_key:
        raise RuntimeError("GOOGLE_API_KEY não configurada")

    manager = data_manager or DataManager()
    bound_tools = tools or build_tools(manager)
    llm = ChatGoogleGenerativeAI(
        model=gemini_model,
        temperature=0,
        google_api_key=google_api_key,
        request_timeout=AGENT_REQUEST_TIMEOUT_SECONDS,
        retries=AGENT_RETRIES,
        thinking_budget=0,
    )
    return llm.bind_tools(bound_tools)


def _selected_credentials() -> tuple[str | None, str]:
    if GEMINI_PROFILE == "alternative":
        return GOOGLE_API_KEY_ALT or GOOGLE_API_KEY, GEMINI_MODEL_ALT
    return GOOGLE_API_KEY, GEMINI_MODEL
