import json
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from app.agent.tools import TOOLS, execute_tool


load_dotenv()

MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.5-flash",
)

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


SYSTEM_PROMPT = """
You are an autonomous senior DevOps incident investigator.

Your job is to investigate a failed Jenkins build and determine
the most likely root cause using the available Jenkins, Git and
Jira tools.

You MUST investigate using evidence.

Investigation rules:

1. Start by getting the Jenkins build information.

2. If the build failed, determine what actually failed.

3. ALWAYS inspect the Jenkins console log when the build result
   alone does not identify the exact failure.

4. If the failure appears related to code changes:
   - identify the last successful build
   - get Git information for both builds
   - compare the commits using git_get_diff

5. Do NOT assume that the latest commit caused the failure.

6. Consider:
   - application code
   - tests
   - dependencies
   - configuration
   - credentials
   - authentication
   - networking
   - Docker
   - Kubernetes
   - Jenkins
   - infrastructure
   - external services

7. Use Jira only when there is evidence that a historical issue
   may help explain the failure.

8. After every tool result, reassess the evidence.

9. Do not repeatedly call the same tool with the same arguments.

10. Do not stop after only seeing Jenkins build metadata if the
    actual failure reason is still unknown.

11. Do not invent evidence.

12. Continue investigating until there is enough evidence for a
    defensible diagnosis.

When investigation is complete, return JSON with:

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


def convert_tools():

    declarations = []

    for tool in TOOLS:

        function = tool["function"]

        declarations.append(
            types.FunctionDeclaration(
                name=function["name"],
                description=function["description"],
                parameters=function["parameters"],
            )
        )

    return [
        types.Tool(
            function_declarations=declarations
        )
    ]


GEMINI_TOOLS = convert_tools()


def investigate(job_name: str, build_number: int):

    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(
                    text=(
                        f"Investigate Jenkins job "
                        f"'{job_name}', build #{build_number}."
                    )
                )
            ],
        )
    ]

    observations = []
    tools_used = []

    max_iterations = 10

    for iteration in range(max_iterations):

        response = client.models.generate_content(
            model=MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=GEMINI_TOOLS,
            ),
        )

        candidate = response.candidates[0]
        model_content = candidate.content

        contents.append(model_content)

        function_calls = []

        for part in model_content.parts:

            if part.function_call:
                function_calls.append(
                    part.function_call
                )

        # -----------------------------------------------------
        # No function call = final answer
        # -----------------------------------------------------

        if not function_calls:

            final_text = response.text

            try:
                investigation = json.loads(final_text)
            except Exception:
                investigation = final_text

            return {
                "job": job_name,
                "build": build_number,
                "iterations": iteration + 1,
                "tools_used": tools_used,
                "observations": observations,
                "investigation": investigation,
                "investigation_complete": True,
            }

        # -----------------------------------------------------
        # Execute requested tools
        # -----------------------------------------------------

        function_response_parts = []

        for call in function_calls:

            tool_name = call.name
            arguments = dict(call.args or {})

            print(
                f"[AGENT] Calling tool: "
                f"{tool_name} {arguments}"
            )

            if tool_name in tools_used:
                previous_calls = [
                    x
                    for x in observations
                    if x["tool"] == tool_name
                    and x["arguments"] == arguments
                ]

                if previous_calls:
                    result = {
                        "error": (
                            "This exact tool call was already "
                            "executed. Use the existing evidence "
                            "and choose a different investigation step."
                        )
                    }

                else:
                    try:
                        result = execute_tool(
                            tool_name,
                            arguments,
                        )
                    except Exception as exc:
                        result = {
                            "error": str(exc)
                        }

            else:

                try:
                    result = execute_tool(
                        tool_name,
                        arguments,
                    )
                except Exception as exc:
                    result = {
                        "error": str(exc)
                    }

            tools_used.append(tool_name)

            observations.append(
                {
                    "tool": tool_name,
                    "arguments": arguments,
                    "result": result,
                }
            )

            function_response_parts.append(
                types.Part.from_function_response(
                    name=tool_name,
                    response={
                        "result": result
                    },
                )
            )

        # -----------------------------------------------------
        # Send tool results back to Gemini
        # -----------------------------------------------------

        contents.append(
            types.Content(
                role="user",
                parts=function_response_parts,
            )
        )

    return {
        "job": job_name,
        "build": build_number,
        "iterations": max_iterations,
        "tools_used": tools_used,
        "observations": observations,
        "investigation": {
            "error": (
                "Investigation stopped because the maximum "
                "number of iterations was reached."
            )
        },
        "investigation_complete": False,
    }