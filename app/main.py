from fastapi import FastAPI

import os

from app.services.git import get_compare_diff

from app.services.jenkins import (
    get_build,
    get_console_log,
    get_git_info,
    get_last_successful_build,
)

from app.investigation.investigator import build_investigation_context

from app.services.jira import search_issues

from app.agent.agent import investigate as investigate_with_agent


app = FastAPI()


@app.get("/")
def root():
    return {
        "message": "Jenkins AI Agent is running"
    }


# ---------------------------------------------------------
# JENKINS
# ---------------------------------------------------------

@app.get("/api/jenkins/build/{job_name}/{build_number}")
def build(
    job_name: str,
    build_number: int,
):
    return get_build(
        job_name,
        build_number,
    )


@app.get("/api/jenkins/build/{job_name}/{build_number}/console")
def console_log(
    job_name: str,
    build_number: int,
):
    return {
        "job": job_name,
        "build": build_number,
        "consoleLog": get_console_log(
            job_name,
            build_number,
        ),
    }


@app.get("/api/jenkins/build/{job_name}/{build_number}/git")
def build_git_info(
    job_name: str,
    build_number: int,
):
    build_data = get_build(
        job_name,
        build_number,
    )

    return get_git_info(build_data)


@app.get("/api/jenkins/build/{job_name}/{build_number}/last-success")
def last_successful_build(
    job_name: str,
    build_number: int,
):
    build = get_last_successful_build(
        job_name,
        build_number,
    )

    return {
        "current_build": build_number,
        "last_successful_build": build["number"],
        "commit": get_git_info(build)["commit"],
    }


@app.get("/api/jenkins/build/{job_name}/{build_number}/diff")
def build_diff(
    job_name: str,
    build_number: int,
):
    current_build = get_build(
        job_name,
        build_number,
    )

    last_successful_build = get_last_successful_build(
        job_name,
        build_number,
    )

    current_git = get_git_info(
        current_build
    )

    successful_git = get_git_info(
        last_successful_build
    )

    return get_compare_diff(
        current_git["repository"],
        successful_git["commit"],
        current_git["commit"],
    )


# ---------------------------------------------------------
# INVESTIGATION CONTEXT
# ---------------------------------------------------------

@app.get("/api/investigate/{job_name}/{build_number}")
def investigate_context(
    job_name: str,
    build_number: int,
):
    return build_investigation_context(
        job_name,
        build_number,
    )


# ---------------------------------------------------------
# JIRA
# ---------------------------------------------------------

@app.get("/api/jira/search")
def jira_search():
    project_key = os.getenv(
        "JIRA_PROJECT_KEY"
    )

    jql = f"project = {project_key}"

    return search_issues(jql)


# ---------------------------------------------------------
# AI AGENT
# ---------------------------------------------------------

@app.get("/api/ai/investigate/{job_name}/{build_number}")
def ai_investigate(
    job_name: str,
    build_number: int,
):
    return investigate_with_agent(
        job_name,
        build_number,
    )

@app.get("/api/agent/investigate/{job_name}/{build_number}")
def agent_investigate(
    job_name: str,
    build_number: int,
):
    return investigate_with_agent(
        job_name,
        build_number,
    )