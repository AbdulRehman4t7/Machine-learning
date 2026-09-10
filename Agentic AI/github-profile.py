import requests


def github_profile(username):
    url = f"https://api.github.com/users/{username}"

    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()

        print("Name:", data["name"])
        print("Username:", data["login"])
        print("Public Repositories:", data["public_repos"])
        print("Followers:", data["followers"])
        print("Following:", data["following"])
    else:
        print("User not found!")


def agent(user_request):

    if "github" in user_request.lower():
        github_profile("AbdulRehman4t7")

    else:
        print("Agent: I don't have a tool for this request yet.")


agent("show me github profile")