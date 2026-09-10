import requests


def github_tool():
    url = "https://api.github.com"

    response = requests.get(url)

    if response.status_code == 200:
        return response.json()

    return "API request failed"


def agent(user_request):

    if "github" in user_request.lower():

        result = github_tool()

        print("\nAgent used: GitHub Tool")

        return result

    return "I don't know which tool to use."


user_input = input("You: ")

result = agent(user_input)

print("\nAgent:", result)