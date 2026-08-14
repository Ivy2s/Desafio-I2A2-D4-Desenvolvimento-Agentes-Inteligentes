from agents.csv_agent import create_agent


agent = create_agent()

response = agent.invoke(
    """
    Quais foram os 5 maiores emitentes
    por valor de nota fiscal em maio de 2025?
    """
)

print(response.content)
print("\n--- TOOL CALLS ---")
print(response.tool_calls)