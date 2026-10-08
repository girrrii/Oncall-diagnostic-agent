from agent import ask

# Each test case defines what the agent's answer MUST contain and MUST NOT contain
# to be considered correct, based on the ground truth in our mock data.
TEST_CASES = [
    {
        "name": "checkout-service: clear deploy correlation",
        "query": "what's happening with checkout-service?",
        "must_include": ["deploy", "14:3"],  # should mention deploy and ~14:30 timeframe
        "must_not_include": ["no open incident found for checkout"],  # sanity check, shouldn't hallucinate an incident
    },
    {
        "name": "auth-service: no false deploy correlation",
        "query": "what about auth-service?",
        "must_include": ["identity provider"],  # should identify the real cause
        "must_not_include": ["caused by the deploy", "due to the deploy", "deploy is likely the cause"],
    },
    {
        "name": "payment-service: existing incident surfaced",
        "query": "what about payment-service?",
        "must_include": ["INC-1042"],
        "must_not_include": ["no data", "14:32:01", "auth-service", "checkout-service"],
    },
    {
        "name": "billing-service: unknown service, no data",
        "query": "what's happening with billing-service?",
        "must_include": ["no data"],
        "must_not_include": ["operating normally", "stable", "healthy"],
    },
    {
        "name": "notification-service: healthy, no issue",
        "query": "what's the status of notification-service?",
        "must_include": ["healthy"],
        "must_not_include": ["no data", "experiencing", "breach"],
    },
    {
        "name": "cross-service: broad status check",
        "query": "which services have issues right now?",
        "must_include": ["checkout-service", "payment-service"],
        "must_not_include": ["auth-service is experiencing", "notification-service is experiencing"],
    },
]

GLOBAL_FORBIDDEN = ["2023"]  # fabricated dates; real data is all 2026

def run_eval():
    results = []
    for case in TEST_CASES:
        print(f"\nRunning: {case['name']}")
        answer = ask(case["query"])
        print(f"Answer: {answer}")

        passed = True
        failures = []

        for phrase in case["must_include"]:
            if phrase.lower() not in answer.lower():
                passed = False
                failures.append(f"Missing expected phrase: '{phrase}'")

        for phrase in case["must_not_include"]:
            if phrase.lower() in answer.lower():
                passed = False
                failures.append(f"Contains forbidden phrase: '{phrase}'")

        for phrase in GLOBAL_FORBIDDEN:
            if phrase in answer:
                passed = False
                failures.append(f"Fabricated date detected: '{phrase}'")

        results.append({
            "name": case["name"],
            "passed": passed,
            "failures": failures,
        })

    print("\n" + "=" * 50)
    print("EVAL SUMMARY")
    print("=" * 50)
    passed_count = sum(1 for r in results if r["passed"])
    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"[{status}] {r['name']}")
        for f in r["failures"]:
            print(f"       - {f}")
    print(f"\n{passed_count}/{len(results)} tests passed")


if __name__ == "__main__":
    run_eval()