import requests
import json

API_URL = "http://localhost:8002"


def test_modify_workflow():
    current_flow = [
        {"type": "click", "selector": "div > button:nth-child(1)"},
        {"type": "input", "selector": "input#search", "value": "test"},
        {"type": "click", "selector": "button#submit"},
    ]

    prompts = [
        "Wrap the first two steps in a loop that repeats 5 times.",
        "Change the selector of the second step to 'input#query'.",
        "Delete the last step.",
        "Add a click step on 'a.link' at the end.",
    ]

    for prompt in prompts:
        print(f"\n--- Testing Prompt: '{prompt}' ---")
        try:
            response = requests.post(
                f"{API_URL}/modify-workflow",
                json={"current_flow": current_flow, "user_prompt": prompt},
            )

            if response.status_code == 200:
                print("Success! Response:")
                print(json.dumps(response.json(), indent=2))
            else:
                print(f"Failed (Status {response.status_code}):")
                print(response.text)

        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    test_modify_workflow()
