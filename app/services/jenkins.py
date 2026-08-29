import os

import requests
from dotenv import load_dotenv


load_dotenv()


JENKINS_URL = os.getenv("JENKINS_URL")
JENKINS_USER = os.getenv("JENKINS_USER")
JENKINS_API_TOKEN = os.getenv("JENKINS_API_TOKEN")


if not JENKINS_URL:
    raise RuntimeError("JENKINS_URL is not configured")

if not JENKINS_USER:
    raise RuntimeError("JENKINS_USER is not configured")

if not JENKINS_API_TOKEN:
    raise RuntimeError("JENKINS_API_TOKEN is not configured")


def get_build(job_name: str, build_number: int):
    url = f"{JENKINS_URL}/job/{job_name}/{build_number}/api/json"

    response = requests.get(
        url,
        auth=(JENKINS_USER, JENKINS_API_TOKEN),
    )

    response.raise_for_status()

    return response.json()

def get_console_log(job_name: str, build_number: int):
    url = f"{JENKINS_URL}/job/{job_name}/{build_number}/consoleText"

    response = requests.get(
        url,
        auth=(JENKINS_USER, JENKINS_API_TOKEN),
    )

    response.raise_for_status()

    return response.text

def get_git_info(build_data: dict):
    git_info = {
        "commit": None,
        "branch": None,
        "repository": None,
        "message": None,
        "changed_files": [],
    }

    for action in build_data.get("actions", []):
        if "lastBuiltRevision" in action:
            revision = action["lastBuiltRevision"]

            if revision:
                git_info["commit"] = revision.get("SHA1")

            branches = revision.get("branch", [])
            if branches:
                git_info["branch"] = branches[0].get("name")

        if "remoteUrls" in action:
            remote_urls = action.get("remoteUrls", [])

            if remote_urls:
                git_info["repository"] = remote_urls[0]

    change_sets = build_data.get("changeSets", [])

    for change_set in change_sets:
        for item in change_set.get("items", []):
            git_info["message"] = item.get("msg")

            for path in item.get("paths", []):
                file_name = path.get("file")

                if file_name:
                    git_info["changed_files"].append(file_name)

    return git_info

def get_last_successful_build(job_name: str, current_build_number: int):
    build_number = current_build_number - 1

    while build_number > 0:
        build = get_build(job_name, build_number)

        if build.get("result") == "SUCCESS":
            return build

        build_number -= 1

    raise RuntimeError(
        f"No successful build found before build #{current_build_number}"
    )