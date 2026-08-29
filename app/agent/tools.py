from app.services.jenkins import (
    get_build,
    get_console_log,
    get_git_info,
    get_last_successful_build,
)

from app.services.git import get_compare_diff
from app.services.jira import search_issues


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "jenkins_get_build",
            "description": (
                "Retrieve metadata about a specific Jenkins build. "
                "Use this as the starting point when investigating a "
                "build. It provides the build result, previous build, "
                "Git change information and test result metadata when "
                "available. This tool tells you WHAT happened at a "
                "high level, but normally does not explain WHY the "
                "build failed."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "job_name": {
                        "type": "string",
                        "description": "Jenkins job name",
                    },
                    "build_number": {
                        "type": "integer",
                        "description": "Jenkins build number",
                    },
                },
                "required": [
                    "job_name",
                    "build_number",
                ],
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "jenkins_get_console_log",
            "description": (
                "Retrieve the Jenkins console log for a build. "
                "This is the primary diagnostic source for determining "
                "WHY a build failed. Use it when the build result is "
                "FAILURE or when the failing stage, error message, "
                "test failure, dependency problem, authentication "
                "problem, deployment problem or infrastructure problem "
                "is not already known. Inspect the log for concrete "
                "error messages and failed stages before deciding "
                "which other tools are needed."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "job_name": {
                        "type": "string",
                        "description": "Jenkins job name",
                    },
                    "build_number": {
                        "type": "integer",
                        "description": "Jenkins build number",
                    },
                },
                "required": [
                    "job_name",
                    "build_number",
                ],
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "jenkins_get_last_successful_build",
            "description": (
                "Find the most recent successful Jenkins build before "
                "the specified build. Use this when comparing a failed "
                "build against a known-good state. This is especially "
                "useful when investigating whether a code/configuration "
                "change introduced the failure. Do NOT assume that the "
                "immediately previous build is the correct baseline "
                "because previous builds may also have failed."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "job_name": {
                        "type": "string",
                        "description": "Jenkins job name",
                    },
                    "build_number": {
                        "type": "integer",
                        "description": "Failed/current Jenkins build number",
                    },
                },
                "required": [
                    "job_name",
                    "build_number",
                ],
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "jenkins_get_git_info",
            "description": (
                "Retrieve the Git repository, branch and commit associated "
                "with a Jenkins build. Use this when Git information is "
                "needed to investigate whether source-code changes may "
                "have contributed to the failure."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "job_name": {
                        "type": "string",
                        "description": "Jenkins job name",
                    },
                    "build_number": {
                        "type": "integer",
                        "description": "Jenkins build number",
                    },
                },
                "required": [
                    "job_name",
                    "build_number",
                ],
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "git_get_diff",
            "description": (
                "Compare two Git commits and return the code changes "
                "between them. Use this when there is evidence that "
                "the failure may be related to source-code or "
                "configuration changes. The recommended comparison "
                "baseline is normally the last successful build's "
                "commit, NOT simply the previous build's commit. "
                "Use the diff as evidence; do not automatically "
                "assume that changed code caused the failure."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "repository": {
                        "type": "string",
                        "description": "Git repository URL",
                    },
                    "base_commit": {
                        "type": "string",
                        "description": "Known-good/reference Git commit",
                    },
                    "target_commit": {
                        "type": "string",
                        "description": "Current failed-build Git commit",
                    },
                },
                "required": [
                    "repository",
                    "base_commit",
                    "target_commit",
                ],
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "jira_search",
            "description": (
                "Search Jira for issues potentially related to the "
                "current incident. Use this when the investigation "
                "would benefit from historical context, known bugs, "
                "existing incidents, dependency problems, deployment "
                "issues or previously reported failures. Search using "
                "specific terms extracted from the Jenkins failure "
                "rather than blindly searching the entire project."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "jql": {
                        "type": "string",
                        "description": (
                            "Jira JQL query targeting potentially "
                            "relevant issues."
                        ),
                    },
                },
                "required": ["jql"],
            },
        },
    },
]


def execute_tool(name: str, arguments: dict):

    if name == "jenkins_get_build":
        return get_build(
            arguments["job_name"],
            arguments["build_number"],
        )

    if name == "jenkins_get_console_log":
        return get_console_log(
            arguments["job_name"],
            arguments["build_number"],
        )

    if name == "jenkins_get_last_successful_build":
        return get_last_successful_build(
            arguments["job_name"],
            arguments["build_number"],
        )

    if name == "jenkins_get_git_info":

        build = get_build(
            arguments["job_name"],
            arguments["build_number"],
        )

        return get_git_info(build)

    if name == "git_get_diff":
        return get_compare_diff(
            arguments["repository"],
            arguments["base_commit"],
            arguments["target_commit"],
        )

    if name == "jira_search":
        return search_issues(
            arguments["jql"]
        )

    raise ValueError(
        f"Unknown tool: {name}"
    )