from langchain_ollama import ChatOllama

llm = ChatOllama(model="qwen2.5:7b")
response = llm.invoke("Say hello in one sentence.")
print(response.content)

from tools import get_logs, get_recent_deploys, check_deploy_correlation

print(get_logs.invoke({"service": "checkout-service"}))
print("---")
print(get_recent_deploys.invoke({"service": "checkout-service"}))
print("---")
print(check_deploy_correlation.invoke({"service": "auth-service", "issue_timestamp": "2026-09-24T10:15:00Z"}))

from tools import get_oncall_person
print(get_oncall_person.invoke({"service": "checkout-service", "timestamp": "2026-09-24T14:32:01Z"}))
print(get_oncall_person.invoke({"service": "checkout-service", "timestamp": "2026-09-24T23:00:00Z"}))