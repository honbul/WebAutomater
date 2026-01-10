import ollama
import json

SYSTEM_PROMPT = """
You are a Workflow Architect for a web scraping automation tool.
Your goal is to modify a given JSON list of browser actions (the "workflow") based on a User Request.

The workflow is a linear list of steps. Example step:
{"type": "click", "selector": "button#login"}

Supported Modification Commands (Output these):
1. WRAP_IN_LOOP: Wrap specific steps in a loop.
   Args: start_index, end_index, loop_selector (optional), count (optional)
   - If user asks to "repeat N times" or "loop N times", you MUST include "count": N.
   - If user asks to "loop through elements" (e.g. products), you MUST include "loop_selector".
   - You MUST provide either 'loop_selector' OR 'count'. Do not provide both unless necessary.
2. CHANGE_SELECTOR: Update the CSS selector for a step.
   Args: step_index, new_selector
3. ADD_STEP: Insert a new step.
   Args: index, step_definition
4. DELETE_STEP: Remove a step.
   Args: index

You must output STRICT JSON only. The output should be a list of commands.

Example 1 (Repeat 5 times):
[
  {"command": "WRAP_IN_LOOP", "start_index": 0, "end_index": 2, "count": 5}
]

Example 2 (Loop over items):
[
  {"command": "WRAP_IN_LOOP", "start_index": 1, "end_index": 3, "loop_selector": ".item"}
]

Do not include markdown formatting (like ```json). Just the raw JSON string.
"""


def modify_workflow(current_flow: list, user_prompt: str) -> list:
    """
    Sends the current workflow and user prompt to Llama 3.1 via Ollama.
    Returns a list of modification commands.
    """

    # Construct the full prompt
    prompt_content = f"""
    Current Workflow:
    {json.dumps(current_flow, indent=2)}

    User Request: "{user_prompt}"

    Generate the modification commands to fulfill the request.
    """

    try:
        response = ollama.chat(
            model="llama3.1:8b",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt_content},
            ],
        )

        content = response["message"]["content"]

        # Clean up potential markdown code blocks if the model outputs them despite instructions
        if content.startswith("```"):
            content = content.strip("`").replace("json\n", "", 1).strip()

        return json.loads(content)

    except Exception as e:
        print(f"Error communicating with AI Agent: {e}")
        # In a real app, handle error gracefully
        return []


if __name__ == "__main__":
    # Test stub
    sample_flow = [
        {"type": "click", "selector": "div.product:nth-of-type(1)"},
        {"type": "click", "selector": "div.product:nth-of-type(2)"},
    ]
    print(
        modify_workflow(
            sample_flow, "Loop through all product items instead of clicking just two."
        )
    )
