from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import StructuredTool

from services.config import GOOGLE_API_KEY
from agents.prompts import SYSTEM_PROMPT
from tools.data_tools import DataQuery, query_data, describe_data


def create_agent():

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        google_api_key=GOOGLE_API_KEY,
    )

    query_tool = StructuredTool.from_function(
        func=query_data,
        name="query_data",
        description="""
        Consulta os dados de notas fiscais.

        Utilize esta ferramenta quando a pergunta do usuário
        exigir informações presentes nos datasets.

        A consulta deve especificar a operação, dataset e,
        quando necessário, período, agrupamento, métrica,
        agregação, ordenação e limite.
        """,
        args_schema=DataQuery,
    )

    describe_tool = StructuredTool.from_function(
        func=describe_data,
        name="describe_data",
        description="""
        Retorna informações sobre os datasets disponíveis,
        incluindo tabelas, colunas e informações relevantes
        para realizar consultas.
        """,
    )

    tools = [
        query_tool,
        describe_tool,
    ]

    llm_with_tools = llm.bind_tools(tools)

    return llm_with_tools