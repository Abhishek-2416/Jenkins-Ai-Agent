import os

from app.services.git import get_compare_diff

from app.services.jenkins import (
    get_build,
    get_console_log,
    get_git_info,
    get_last_successful_build,
)

from app.services.jira import search_issues


def build_investigation_context(job_name: str, build_number: int):
    # Current build
    current_build = get_build(job_name, build_number)

    # Last known-good build
    last_successful_build = get_last_successful_build(
        job_name,
        build_number,
    )

    # Git information
    current_git = get_git_info(current_build)
    successful_git = get_git_info(last_successful_build)

    # Git diff
    diff = get_compare_diff(
        current_git["repository"],
        successful_git["commit"],
        current_git["commit"],
    )

    # Changed files
    changes = []

    for file in diff.get("files", []):
        changes.append(
            {
                "file": file.get("filename"),
                "status": file.get("status"),
                "patch": file.get("patch"),
            }
        )

    # Jira search
    jira_issues = []

    project_key = os.getenv("JIRA_PROJECT_KEY")

    search_terms = []

    if current_git.get("message"):
        search_terms.append(current_git["message"])

    for change in changes:
        if change.get("file"):
            search_terms.append(change["file"])

    for term in search_terms:
        # Jira text search works better with individual words
        words = term.replace("/", " ").replace("_", " ").split()

        for word in words:
            if len(word) >= 4:
                jql = f'project = {project_key} AND text ~ "{word}"'

                result = search_issues(
                    jql,
                    max_results=5,
                )

                for issue in result.get("issues", []):
                    if issue not in jira_issues:
                        jira_issues.append(issue)

    # Test information
    test_results = {
        "failed": 0,
        "passed": 0,
        "skipped": 0,
        "total": 0,
    }

    for action in current_build.get("actions", []):
        if action.get("_class") == "hudson.plugins.junit.TestResultAction":
            test_results["failed"] = action.get("failCount", 0)
            test_results["skipped"] = action.get("skipCount", 0)
            test_results["total"] = action.get("totalCount", 0)

            test_results["passed"] = (
                test_results["total"]
                - test_results["failed"]
                - test_results["skipped"]
            )

    print("=== JIRA SEARCH TERMS ===")
    print(search_terms)

    return {
        "build": {
            "job": job_name,
            "number": build_number,
            "status": current_build.get("result"),
        },
        "last_successful_build": {
            "number": last_successful_build.get("number"),
            "commit": successful_git.get("commit"),
        },
        "current_commit": {
            "sha": current_git.get("commit"),
            "message": current_git.get("message"),
            "branch": current_git.get("branch"),
            "repository": current_git.get("repository"),
        },
        "changes": changes,
        "jira_issues": jira_issues,
        "test_results": test_results,
        "console_log": get_console_log(
            job_name,
            build_number,
        ),
    }
