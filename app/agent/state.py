class InvestigationState:

    def __init__(self, job_name: str, build_number: int):
        self.job_name = job_name
        self.build_number = build_number

        self.observations = []
        self.tools_used = []

    def add_observation(self, tool_name: str, result):
        self.observations.append(
            {
                "tool": tool_name,
                "result": result,
            }
        )

        self.tools_used.append(tool_name)

    def as_dict(self):
        return {
            "job_name": self.job_name,
            "build_number": self.build_number,
            "observations": self.observations,
            "tools_used": self.tools_used,
        }