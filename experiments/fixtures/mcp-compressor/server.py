from typing import Literal

from mcp.server.fastmcp import FastMCP


server = FastMCP("synthetic-tools")
DOMAINS = ("build", "test", "deploy", "docs", "security", "metrics", "release", "review")


def register(domain: str) -> None:
    def inspect_record(
        record_id: str,
        mode: Literal["summary", "full"] = "summary",
        include_history: bool = False,
        threshold: float = 0.5,
    ) -> str:
        return f"{domain}:{record_id}:{mode}:{include_history}:{threshold}"

    server.tool(
        name=f"inspect_{domain}",
        description=(
            f"Inspect the synthetic {domain} record and return its deterministic status. "
            "Use this when evaluating a local benchmark record by identifier. "
            "The mode selects summary or full output, include_history controls historical "
            "details, and threshold sets the comparison cutoff. "
            "This tool has no network access or side effects."
        ),
    )(inspect_record)


for item in DOMAINS:
    register(item)


if __name__ == "__main__":
    server.run(transport="stdio")
