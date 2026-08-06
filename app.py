from services.config import GOOGLE_API_KEY
from agents.csv_agent import create_agent

def main():
    print("Iniciando Agente CSV...")

    agent = create_agent()

    print("Agente iniciado com sucesso!")

if __name__ == "__main__":
    main()