from langchain_core.tools import StructuredTool
from langchain_google_genai import ChatGoogleGenerativeAI

from pipeline.data_manager import DataManager
from services.config import (
    AGENT_REQUEST_TIMEOUT_SECONDS,
    AGENT_RETRIES,
    GOOGLE_API_KEY,
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
    if not GOOGLE_API_KEY:
        raise RuntimeError("GOOGLE_API_KEY não configurada")

    manager = data_manager or DataManager()
    bound_tools = tools or build_tools(manager)
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        google_api_key=GOOGLE_API_KEY,
        request_timeout=AGENT_REQUEST_TIMEOUT_SECONDS,
        retries=AGENT_RETRIES,
    )
    return llm.bind_tools(bound_tools)
