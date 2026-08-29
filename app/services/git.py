import requests

# Here what are we doing is 
#We're converting:
#https://github.com/Abhishek-2416/ai-jenkins-demo-node
#into:
#Abhishek-2416/ai-jenkins-demo-node
#Then we're calling GitHub's compare API:
#GET
#/repos/Abhishek-2416/ai-jenkins-demo-node/compare/<old>...<new>


def get_compare_diff(repository_url: str, base_commit: str, head_commit: str):
    repository = repository_url.rstrip("/")

    if repository.endswith(".git"):
        repository = repository[:-4]

    repository = repository.replace("https://github.com/", "")

    url = f"https://api.github.com/repos/{repository}/compare/{base_commit}...{head_commit}"

    response = requests.get(url)

    response.raise_for_status()

    return response.json()