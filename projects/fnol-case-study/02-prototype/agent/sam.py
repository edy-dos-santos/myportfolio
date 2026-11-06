"""Sam, the FNOL claims assistant, on the Claude Agent SDK.

Run a live chat in the terminal:  python agent/sam.py [v1|v2]
"""
import asyncio
import sys
from pathlib import Path

from claude_agent_sdk import (AssistantMessage, ClaudeAgentOptions, ClaudeSDKClient, ResultMessage,
                              SystemMessage, TextBlock, ToolUseBlock)

sys.path.insert(0, str(Path(__file__).parent))
from tools import ALLOWED, DATA, SERVER, ToolState, build_server  # noqa: E402

MODEL = "claude-opus-5-5"
EFFORT = "low"  # chat latency matters more than depth here

# Each version = a system prompt + which code-level guardrails are switched on.
VERSIONS = {
    "v1": {"prompt": "system_v1.md", "guards": {}},
    "v2": {"prompt": "system_v2.md", "guards": {"require_verified": True, "confirm_before_lodge": True,
                                                 "handoff_fields": True, "log_complaint": True,
                                                 "strict_identity": True}},
}


def system_prompt(version):
    text = (Path(__file__).parent / "prompts" / VERSIONS[version]["prompt"]).read_text(encoding="utf-8")
    return text.replace("{today}", DATA["today"]).replace("{timezone}", DATA["timezone"])


def build_options(version, state: ToolState, cwd):
    state.guards = VERSIONS[version]["guards"]
    return ClaudeAgentOptions(
        system_prompt=system_prompt(version),
        model=MODEL, effort=EFFORT,
        tools=[],                       # no built-in Claude Code tools
        mcp_servers={SERVER: build_server(state)}, strict_mcp_config=True,
        allowed_tools=ALLOWED, setting_sources=[],
        max_turns=12, cwd=str(cwd),
    )


async def ask(client, text, state=None):
    """Send one customer message; return Sam's reply text and the tool calls made."""
    if state is not None:          # lets tools know which customer turn this is (confirmation gate)
        state.turn += 1
        state.last_customer_text = text
    await client.query(text)
    reply, tools = [], []
    async for m in client.receive_response():
        if isinstance(m, AssistantMessage):
            for b in m.content:
                if isinstance(b, TextBlock):
                    reply.append(b.text)
                elif isinstance(b, ToolUseBlock):
                    tools.append(b.name.removeprefix(f"mcp__{SERVER}__"))
        elif isinstance(m, SystemMessage) and m.subtype == "init":
            status = {s.get("name"): s.get("status") for s in m.data.get("mcp_servers", [])}
            if status.get(SERVER) not in (None, "connected"):
                raise RuntimeError(f"tool server not connected: {status}")
        elif isinstance(m, ResultMessage) and m.is_error:
            reply.append(f"[agent error: {m.subtype}]")
    return "\n\n".join(reply).strip(), tools


async def main(version):
    state = ToolState()
    async with ClaudeSDKClient(options=build_options(version, state, Path.cwd())) as client:
        print(f"Sam ({version}). Type 'quit' to exit.\n")
        while (text := input("You: ").strip()) != "quit":
            reply, tools = await ask(client, text, state)
            if tools:
                print(f"  [tools: {', '.join(tools)}]")
            print(f"Sam: {reply}\n")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "v2"))
