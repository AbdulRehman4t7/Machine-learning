import re
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

    print("\nUser Request:", request)

    request_lower = request.lower()

    # Find numbers
    numbers = re.findall(r"\d+(?:\.\d+)?", request_lower)

    if len(numbers) < 2:
        return "Please provide two numbers."

    a = float(numbers[0])
    b = float(numbers[1])

    # Decide operation
    if "add" in request_lower:
        operation = "add"

    elif "subtract" in request_lower:
        operation = "subtract"

    elif "multiply" in request_lower:
        operation = "multiply"

    elif "divide" in request_lower:
        operation = "divide"

    else:
        return "I don't know which operation to use."

    # Create structured decision
    tool_request = {
        "tool": "calculator",
        "operation": operation,
        "a": a,
        "b": b
    }

    print("\nAgent Decision:")

    print(json.dumps(tool_request, indent=4))

    # Execute tool
    result = calculator(
        tool_request["a"],
        tool_request["b"],
        tool_request["operation"]
    )

    return result


while True:

    user_input = input("\nYou: ")

    if user_input.lower() == "exit":
        print("Agent: Goodbye!")
        break

    answer = agent(user_input)

    print("\nAgent:", answer)