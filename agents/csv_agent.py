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
        Consulta dados de qualquer dataset carregado.

        IMPORTANTE:
        Antes de utilizar esta ferramenta, consulte describe_data para
        identificar os datasets e as colunas reais disponíveis.

        NUNCA invente nomes de colunas ou datasets.

        Os argumentos dataset, group_by, metric e sort devem utilizar
        EXATAMENTE os nomes retornados por describe_data.

        A ferramenta suporta:
        - count: contagem de registros;
        - list: listagem de registros;
        - aggregate: agregações como sum, mean, min e max.

        Para aggregate, informe:
        - dataset
        - group_by
        - metric
        - aggregation
        - sort, quando necessário
        - limit, quando necessário

        O sistema pode receber qualquer arquivo ZIP contendo um ou
        vários CSVs. Não assuma uma estrutura específica de dados.
        """,
        args_schema=DataQuery,
    )

    describe_tool = StructuredTool.from_function(
        func=describe_data,
        name="describe_data",
        description="""
        Consulta o schema dos dados atualmente carregados.

        Retorna os datasets disponíveis, número de registros, nomes das
        colunas, tipos de dados e amostras dos registros.

        Utilize esta ferramenta ANTES de query_data para descobrir quais
        datasets e colunas devem ser utilizados.

        Os nomes dos datasets e colunas são dinâmicos e podem variar
        completamente entre diferentes arquivos ZIP.
        """,
    )

    tools = [
        describe_tool,
        query_tool,
    ]

    llm_with_tools = llm.bind_tools(tools)

    return llm_with_tools