import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from agents.csv_agent import build_tools, create_agent
from agents.prompts import SYSTEM_PROMPT
from services.config import is_ai_configured
from services.exceptions import (
    AIUnavailableError,
    AgentExecutionError,
    AgentIterationLimitError,
)
from services.session_registry import SessionRegistry


@dataclass
class QueryResult:
    answer: str
    data: dict[str, Any] | None


class QueryService:
    def __init__(self, registry: SessionRegistry, max_iterations: int = 5):
        self.registry = registry
        self.max_iterations = max_iterations

    def query(self, dataset_id: UUID, question: str) -> QueryResult:
        session = self.registry.get(dataset_id)
        if not is_ai_configured():
            raise AIUnavailableError("O provedor de IA não está configurado")

        tools = build_tools(session.manager)
        tool_map = {tool.name: tool for tool in tools}
        try:
            agent = create_agent(session.manager, tools=tools)
            messages = [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=question),
            ]
            last_tool_result: dict[str, Any] | None = None

            for _ in range(self.max_iterations):
                response = agent.invoke(messages)
                messages.append(response)
                tool_calls = getattr(response, "tool_calls", []) or []
                if not tool_calls:
                    return QueryResult(
                        answer=self._content_as_text(response.content),
                        data=self._result_as_data(last_tool_result),
                    )

                for tool_call in tool_calls:
                    tool_name = tool_call["name"]
                    if tool_name not in tool_map:
                        raise AgentExecutionError(f"Ferramenta desconhecida: {tool_name}")
                    result = tool_map[tool_name].invoke(tool_call.get("args", {}))
                    last_tool_result = result if isinstance(result, dict) else None
                    messages.append(
                        ToolMessage(
                            content=json.dumps(result, ensure_ascii=False, default=str),
                            tool_call_id=tool_call["id"],
                        )
                    )

            raise AgentIterationLimitError("O agente excedeu o limite de iterações")
        except (AIUnavailableError, AgentExecutionError):
            raise
        except Exception as error:
            raise AgentExecutionError("Falha ao executar a consulta") from error

    @staticmethod
    def _content_as_text(content: Any) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "".join(
                item.get("text", "") if isinstance(item, dict) else str(item)
                for item in content
            )
        return str(content)

    @staticmethod
    def _result_as_data(result: dict[str, Any] | None) -> dict[str, Any] | None:
        if not result:
            return None
        operation = result.get("operation")
        value = result.get("result")
        if operation == "count":
            return {"type": "count", "value": value}
        if isinstance(value, list):
            columns = list(value[0].keys()) if value else []
            return {"type": "table", "columns": columns, "rows": value}
        return None
