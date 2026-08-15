import json
import logging
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from agents.csv_agent import build_tools, create_agent
from agents.prompts import SYSTEM_PROMPT
from services.config import is_ai_configured
from services.json_safe import to_json_safe
from services.exceptions import (
    AIUnavailableError,
    AgentExecutionError,
    AgentIterationLimitError,
    AgentTimeoutError,
    ToolExecutionError,
    UnknownToolError,
)
from services.session_registry import SessionRegistry

logger = logging.getLogger(__name__)


@dataclass
class QueryResult:
    answer: str
    data: dict[str, Any] | None


class QueryService:
    def __init__(self, registry: SessionRegistry, max_iterations: int | None = None):
        self.registry = registry
        from services.config import MAX_AGENT_ITERATIONS

        self.max_iterations = max_iterations or MAX_AGENT_ITERATIONS

    def query(self, dataset_id: UUID, question: str) -> QueryResult:
        session = self.registry.get(dataset_id)
        if not is_ai_configured():
            raise AIUnavailableError("O provedor de IA não está configurado")

        logger.info("agent query started dataset_id=%s", dataset_id)
        tools = build_tools(session.manager)
        tool_map = {tool.name: tool for tool in tools}
        try:
            agent = create_agent(session.manager, tools=tools)
            messages = [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=question),
            ]
            last_tool_result: dict[str, Any] | None = None

            for iteration in range(1, self.max_iterations + 1):
                logger.info("agent iteration=%d dataset_id=%s", iteration, dataset_id)
                try:
                    response = agent.invoke(messages)
                except TimeoutError as error:
                    raise AgentTimeoutError("O provedor excedeu o tempo limite") from error
                messages.append(response)
                tool_calls = getattr(response, "tool_calls", []) or []
                if not tool_calls:
                    logger.info("agent query finished dataset_id=%s", dataset_id)
                    return QueryResult(
                        answer=self._content_as_text(response.content),
                        data=self._result_as_data(last_tool_result),
                    )

                for tool_call in tool_calls:
                    tool_name = tool_call["name"]
                    if tool_name not in tool_map:
                        raise UnknownToolError(f"Ferramenta desconhecida: {tool_name}")
                    logger.info("agent tool=%s dataset_id=%s", tool_name, dataset_id)
                    try:
                        result = tool_map[tool_name].invoke(tool_call.get("args", {}))
                    except Exception as error:
                        raise ToolExecutionError(
                            f"Falha ao executar a ferramenta: {tool_name}"
                        ) from error
                    last_tool_result = result if isinstance(result, dict) else None
                    messages.append(
                        ToolMessage(
                            content=json.dumps(result, ensure_ascii=False, default=str),
                            tool_call_id=tool_call["id"],
                        )
                    )

            logger.warning("agent iteration limit dataset_id=%s", dataset_id)
            raise AgentIterationLimitError("O agente excedeu o limite de iterações")
        except (AIUnavailableError, AgentExecutionError):
            raise
        except Exception as error:
            logger.exception("agent query failed dataset_id=%s", dataset_id)
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
            return {"type": "count", "value": int(to_json_safe(value))}
        if isinstance(value, list):
            rows = to_json_safe(value)
            columns = []
            for row in rows:
                for column in row:
                    if column not in columns:
                        columns.append(column)
            return {
                "type": "table",
                "columns": columns,
                "rows": rows,
                "truncated": bool(result.get("truncated", False)),
                "returnedRows": int(result.get("returned_rows", len(rows))),
            }
        return None
