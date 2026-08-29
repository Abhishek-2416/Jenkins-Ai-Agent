import os

from dotenv import load_dotenv
from google import genai


load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.5-flash",
)

if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is not configured"
    )


client = genai.Client(
    api_key=GEMINI_API_KEY
)


SYSTEM_PROMPT = """
You are an autonomous senior DevOps incident investigator.

Your job is to investigate failed CI/CD builds and determine
the most likely root cause using available tools.

You have access to tools for systems such as:

- Jenkins
- Git
- Jira
- Kubernetes
- infrastructure
- external services

You must reason about what information you currently have
and decide which tool should be called next.

IMPORTANT RULES:

1. Do not assume the latest Git commit caused the failure.

2. Do not assume the failure is a code problem.

3. Consider different possible causes including:
   - application code
   - tests
   - compilation
   - dependencies
   - configuration
   - credentials
   - authentication
   - network
   - Docker
   - Kubernetes
   - Jenkins
   - infrastructure
   - external services

4. Start with the most useful source of evidence.

5. Use the Jenkins console log when the build metadata does
   not explain the failure.

6. If the failure appears related to code changes, investigate
   the last successful build and compare the commits.

7. If the failure appears unrelated to code, investigate the
   appropriate infrastructure or external-system evidence.

8. Do not blindly call every available tool.

9. After every tool result, reassess the evidence and decide
   what should happen next.

10. You may call multiple tools.

11. Continue investigating until there is enough evidence for
    a defensible diagnosis.

12. Distinguish facts from hypotheses.

13. Never invent evidence.

14. If evidence is insufficient, explicitly say so.

15. The final answer must explain WHY the root cause was selected.

When the investigation is complete, return structured JSON:

{
    "summary": "...",
    "failed_stage": "...",
    "root_cause": "...",
    "root_cause_category": "...",
    "evidence": [],
    "recent_change_responsible": true,
    "affected_files": [],
    "recommended_fix": "...",
    "confidence": "high|medium|low",
    "related_jira_issues": [],
    "investigation_complete": true
}
"""


def chat(messages, tools=None):

    contents = []

    for message in messages:

        role = message.get("role")

        if role == "system":
            continue

        contents.append(
            {
                "role": (
                    "model"
                    if role == "assistant"
                    else "user"
                ),
                "parts": [
                    {
                        "text": message.get(
                            "content",
                            ""
                        )
                    }
                ],
            }
        )

    config = {
        "system_instruction": SYSTEM_PROMPT,
    }

    # Tool support will be wired into the agent layer.
    # For now this provides the Gemini chat interface.
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=contents,
        config=config,
    )

    return response