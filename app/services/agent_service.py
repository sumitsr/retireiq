import requests
import json
import time
import os
import browser_cookie3


def generateAgentAPIToken():
    target_domain = "https://dev.lionis.ai/error/500?status=success"
    try:
        cookies = browser_cookie3.load(domain_name=target_domain)
        for cookie in cookies:
            print(f"{cookie.name} = {cookie.value}")
    except Exception as e:
        print(f"Error loading cookies: {e}")


def call_agent_api(intent="", user_id=""):
    agentUrl = "https://dev.lionis.ai/api/v1/agents/68259fbd69d8809665943d87/query"
    token = os.environ.get("LIONIS_AGENT_TOKEN")
    headers = {
        "x-client-id": "7b4e7797-1bdf-40a0-908f-4827041f4b99",
        "x-project-id": "e317e372-b9a8-43c1-bfbb-0bf9e472a49d",
        "x-workspace-id": "8e4e13b7-41bf-4f51-a797-652c6f32d176",
        "accept": "application/json",
        "Content-Type": "application/json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    user_intent = (
        f"intent: {intent.get('intent', '')}, sub-intent: {intent.get('sub_intent', '')}"
        if isinstance(intent, dict)
        else intent
    )
    data = {"input_params": {"user_intent": user_intent, "user_id": str(user_id)}}
    print("Agent API payload")
    print(json.dumps(data, indent=4))

    response = requests.post(agentUrl, headers=headers, json=data)

    print(f"Status Code: {response.status_code}")
    print("Response Body:")
    print(response.json())

    if response.status_code == 200:
        res = response.json()
        event_res = call_agent_api_get_final_response(res.get("correlation_id"))
        print("event_res:")
        print(event_res)
        return event_res
    else:
        return "Something went wrong, Please try again."


def call_agent_api_get_final_response(correlation_id):
    agentUrl = f"https://dev.lionis.ai/api/v1/events/events?correlationId={correlation_id}"
    token = os.environ.get("LIONIS_EVENT_TOKEN")
    headers = {
        "x-client-id": "7b4e7797-1bdf-40a0-908f-4827041f4b99",
        "x-project-id": "e317e372-b9a8-43c1-bfbb-0bf9e472a49d",
        "x-workspace-id": "8e4e13b7-41bf-4f51-a797-652c6f32d176",
        "accept": "application/json",
        "Content-Type": "application/json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    response = requests.get(agentUrl, headers=headers)
    if response.status_code == 200:
        print(f"Event Status Code: {response.status_code}")
        res = response.json()
        print(res)

        if res and len(res) > 0:
            agent_status = res[0].get("agentStatus")
            print(f"agentStatus: {agent_status}")

            if agent_status == "completed":
                out = res[0].get("output", {}).get("response_text", "")
                print("output:")
                print(out)
                return out
            else:
                time.sleep(5)
                return call_agent_api_get_final_response(correlation_id)
        return "Empty response from event queue"
    else:
        return "Something went wrong, Please try again."
