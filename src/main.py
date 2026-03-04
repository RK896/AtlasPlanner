from src.graph.workflow import app
from langchain_core.messages import HumanMessage, AIMessage
import asyncio

def print_separator():
    print("\n" + "="*80 + "\n")

async def main():
    print("🗺️  AtlasPlanner - Multi-Agent Travel Planner")
    print("="*80)
    print("Chat with our travel planning agents!")
    print("Type 'quit' or 'exit' to end the conversation")
    print_separator()

    # Track conversation state
    state = {"messages": []}

    while True:
        # Get user input
        user_input = input("You: ").strip()

        if user_input.lower() in ['quit', 'exit', 'q']:
            print("\n👋 Thanks for using AtlasPlanner! Safe travels!")
            break

        if not user_input:
            continue

        # Add user message to state
        state["messages"].append(HumanMessage(content=user_input))

        # Invoke the graph
        prev_count = len(state["messages"])
        result = await app.ainvoke(state)

        # Update state with result
        state = result

        # Display responses
        print_separator()

        # Find and display all AI responses after the user's message
        for msg in state["messages"][prev_count:]:  # Look at recent messages
            if isinstance(msg, AIMessage) and msg.content:
                print(f"🤖 Agent: {msg.content}")
                print()

        print_separator()

if __name__ == "__main__":
    asyncio.run(main())