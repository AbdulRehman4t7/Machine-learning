import json


def calculator(a, b, operation):
    if operation == "add":
        return a + b

    elif operation == "subtract":
        return a - b

    elif operation == "multiply":
        return a * b

    elif operation == "divide":
        if b == 0:
            return "Cannot divide by zero."

        return a / b

    return "Unknown operation"


def agent(request):
    print("User Request:", request)

    # Agent's decision
    tool_request = {
        "tool": "calculator",
        "operation": "add",
        "a": 20,
        "b": 30
    }

    print("\nAgent Decision:")

    print(json.dumps(tool_request, indent=4))

    # Execute selected tool
    result = calculator(
        tool_request["a"],
        tool_request["b"],
        tool_request["operation"]
    )

    return result


answer = agent("Please add 20 and 30")

print("\nFinal Answer:", answer)