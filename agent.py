from langgraph.prebuilt import create_react_agent
from langchain_ollama import ChatOllama
from tools import get_logs, get_metrics, get_recent_deploys, get_open_incidents, check_deploy_correlation, get_oncall_person, get_all_services_status
from prompts import SYSTEM_PROMPT

llm = ChatOllama(model="qwen2.5:7b", temperature=0)

tools = [get_logs, get_metrics, get_recent_deploys, get_open_incidents, check_deploy_correlation, get_oncall_person, get_all_services_status]

agent = create_react_agent(llm, tools, prompt=SYSTEM_PROMPT)


def ask(query: str):
    result = agent.invoke({"messages": [{"role": "user", "content": query}]})
    final_message = result["messages"][-1]
    return final_message.content


if __name__ == "__main__":
    print("=" * 60)
    print("  ON-CALL DIAGNOSTIC AGENT")
    print("  Ask about any service's status, or type 'exit' to quit.")
    print("=" * 60)

    while True:
        query = input("\n> ")
        if query.lower() in ("exit", "quit"):
            print("\nGoodbye.")
            break
        if not query.strip():
            continue

        print("\nInvestigating...\n")
        answer = ask(query)
        print("-" * 60)
        print(answer)
        print("-" * 60)