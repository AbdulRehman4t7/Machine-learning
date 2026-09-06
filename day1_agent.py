import re


def calculator(a, b, operation):
    if operation == "add":
        return a + b

    elif operation == "subtract":
        return a - b

    elif operation == "multiply":
        return a * b

    elif operation == "divide":
        return a / b

    return "Unknown operation"


def greeting():
    return "Hello! I am your AI Agent."


def agent(user_request):
    request = user_request.lower()

    # Greeting
    if "hello" in request or "hi" in request or "helo" in request:
        return greeting()

    # Extract numbers from user request
    numbers = re.findall(r"\d+(?:\.\d+)?", request)

    if len(numbers) < 2:
        return "Please provide two numbers."

    a = float(numbers[0])
    b = float(numbers[1])

    # Addition
    if "add" in request:
        result = calculator(a, b, "add")
        return f"The answer is {result:g}"

    # Multiplication
    elif "multiply" in request:
        result = calculator(a, b, "multiply")
        return f"The answer is {result:g}"

    # Subtraction
    elif "subtract" in request:
        result = calculator(a, b, "subtract")
        return f"The answer is {result:g}"

    # Division
    elif "divide" in request:
        if b == 0:
            return "Cannot divide by zero."

        result = calculator(a, b, "divide")
        return f"The answer is {result:g}"

    else:
        return "I don't know which tool to use."


while True:
    user_input = input("\nYou: ")

    if user_input.lower() == "exit":
        print("Agent: Goodbye!")
        break

    response = agent(user_input)

    print("Agent:", response)