"""AtlasPlanner command-line chat.

    python -m src.main                     # new session
    python -m src.main --session lisbon    # create or resume a named session
"""
import argparse
import asyncio
import sys
import uuid

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.status import Status

from src.agents.messages import MASTER_NAME
from src.graph.workflow import compile_app
from src.utils.config import API_KEY, PROJECT_ROOT
from src.utils.itinerary import save_itinerary
from src.utils.logger import configure_logging

SESSIONS_DB = PROJECT_ROOT / ".atlas" / "sessions.db"
ITINERARY_DIR = PROJECT_ROOT / "itineraries"
EXIT_COMMANDS = {"/quit", "/exit", "quit", "exit", "q"}
TASK_PREVIEW_CHARS = 70
AGENT_ICONS = {"research": "🔎", "flights": "✈️", "hotels": "🏨", "activities": "🎟️", "respond": "📝"}
HELP_TEXT = """\
**Ask anything about a trip**, for example:
- *Plan 5 days in Kyoto from SFO, April 10-15 2027, I love food and temples*
- *What's the weather like in Lisbon next week?*
- *Find one-way flights JFK to LIS on 2027-03-03*

**Commands**
- `/save [name]`: save the latest plan to `itineraries/` as Markdown
- `/new`: start a fresh session
- `/help`: show this help
- `/quit`: exit (sessions are saved; resume with `--session <id>`)"""

console = Console()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AtlasPlanner: multi-agent travel planner")
    parser.add_argument("--session", help="session id to create or resume")
    parser.add_argument("--verbose", action="store_true", help="show agent/tool logs")
    return parser.parse_args()


def new_session_id() -> str:
    return f"trip-{uuid.uuid4().hex[:6]}"


async def run_turn(app, config: dict, user_input: str) -> str:
    """Stream one user turn through the graph, showing which agent is working."""
    inputs = {"messages": [HumanMessage(content=user_input)], "visited": []}
    reply = ""
    with console.status("[bold cyan]Planning…") as status:
        async for chunk in app.astream(inputs, config, stream_mode="updates"):
            for node, update in chunk.items():
                reply = show_progress(node, update, status) or reply
    return reply


def show_progress(node: str, update: dict, status: Status) -> str | None:
    """Update the spinner for router decisions; return the reply when it's ready."""
    if node == "router":
        agent = update["next_agent"]
        task = update.get("task", "")[:TASK_PREVIEW_CHARS]
        label = "writing your answer" if agent == "respond" else f"{agent} agent: {task}"
        status.update(f"{AGENT_ICONS.get(agent, '•')}  {label}")
        return None
    if node == "respond":
        return update["messages"][-1].content
    console.print(f"  [dim]{AGENT_ICONS.get(node, '•')}  {node} agent reported back[/dim]")
    return None


async def last_master_reply(app, config: dict) -> tuple[str, int]:
    """Return (latest planner reply, message count) for a saved session."""
    snapshot = await app.aget_state(config)
    messages = snapshot.values.get("messages", []) if snapshot.values else []
    replies = [m.content for m in messages if isinstance(m, AIMessage) and m.name == MASTER_NAME]
    return (replies[-1] if replies else ""), len(messages)


def handle_save(argument: str, last_reply: str, session_id: str) -> None:
    try:
        path = save_itinerary(last_reply, ITINERARY_DIR, argument or session_id)
    except (ValueError, OSError) as error:
        console.print(f"[yellow]{error}[/yellow]")
        return
    console.print(f"[green]Saved to {path.relative_to(PROJECT_ROOT)}[/green]")


def print_session(session_id: str, message_count: int) -> None:
    resumed = f", resumed with {message_count} messages" if message_count else ""
    console.print(f"[dim]Session [bold]{session_id}[/bold]{resumed}. "
                  f"Resume later with: python -m src.main --session {session_id}[/dim]\n")


async def chat(app, session_id: str) -> None:
    config = {"configurable": {"thread_id": session_id}}
    last_reply, message_count = await last_master_reply(app, config)
    print_session(session_id, message_count)

    while True:
        try:
            user_input = (await asyncio.to_thread(console.input, "[bold green]You ›[/] ")).strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not user_input:
            continue

        command, _, argument = user_input.partition(" ")
        command = command.lower()
        if command in EXIT_COMMANDS:
            break
        if command == "/help":
            console.print(Markdown(HELP_TEXT))
        elif command == "/save":
            handle_save(argument.strip(), last_reply, session_id)
        elif command == "/new":
            session_id, last_reply = new_session_id(), ""
            config = {"configurable": {"thread_id": session_id}}
            print_session(session_id, 0)
        else:
            reply = await run_turn(app, config, user_input)
            last_reply = reply or last_reply
            console.print(Panel(Markdown(reply), title="🗺️  AtlasPlanner", border_style="cyan"))


async def main() -> None:
    args = parse_args()
    configure_logging(args.verbose)
    if not API_KEY:
        console.print("[red]ANTHROPIC_API_KEY is not set. Copy .env.example to .env and add your key.[/red]")
        sys.exit(1)

    console.print(Panel.fit("[bold]🗺️  AtlasPlanner[/bold]: multi-agent travel planner\n"
                            "Research · Flights · Hotels · Activities   (type /help)", border_style="cyan"))
    SESSIONS_DB.parent.mkdir(parents=True, exist_ok=True)
    async with AsyncSqliteSaver.from_conn_string(str(SESSIONS_DB)) as checkpointer:
        await chat(compile_app(checkpointer=checkpointer), args.session or new_session_id())
    console.print("\n👋 Thanks for using AtlasPlanner. Safe travels!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n👋 Bye!")
