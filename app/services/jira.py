import os

import requests
from dotenv import load_dotenv


load_dotenv()

JIRA_URL = os.getenv("JIRA_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY")


def search_issues(jql: str, max_results: int = 10):
    url = f"{JIRA_URL}/rest/api/3/search/jql"

    response = requests.get(
        url,
        params={
            "jql": jql,
            "maxResults": max_results,
            "fields": "summary,description,status,issuetype,priority",
        },
        auth=(JIRA_EMAIL, JIRA_API_TOKEN),
        headers={
            "Accept": "application/json",
        },
    )

    response.raise_for_status()

    return response.json()