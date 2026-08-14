from agents.csv_agent import create_agent
from tools.data_tools import query_data, describe_data, DataQuery


agent = create_agent()

question = (
    "Quais são os 5 fornecedores com maior valor total?"
)

messages = [question]

for step in range(5):

    response = agent.invoke(messages)

    print(f"\n=== ETAPA {step + 1} ===")

    # Agente terminou
    if not response.tool_calls:
        print("\n=== RESPOSTA FINAL ===")
        print(response.content)
        break

    print("=== TOOL CALL ===")
    print(response.tool_calls)

    # Adiciona resposta do agente ao histórico
    messages.append(response)

    # Executa as ferramentas solicitadas
    for tool_call in response.tool_calls:

        tool_name = tool_call["name"]

        if tool_name == "describe_data":

            tool_result = describe_data()

        elif tool_name == "query_data":

            query = DataQuery(**tool_call["args"])
            tool_result = query_data(query)

        else:
            raise ValueError(
                f"Tool desconhecida: {tool_name}"
            )

        print("\n=== RESULTADO DA TOOL ===")
        print(tool_result)

        messages.append(
            {
                "role": "tool",
                "content": str(tool_result),
                "tool_call_id": tool_call["id"],
            }
        )

else:
    print("\nO agente atingiu o limite de etapas.")