from langgraph.graph import MessagesState
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, ToolMessage
from src.utils.config import API_KEY, MODEL_CONFIG
from langchain_mcp_adapters.client import MultiServerMCPClient


# Create model with tools bound
base_model = ChatAnthropic(
    api_key = API_KEY,
    model = MODEL_CONFIG["model"],
    temperature=MODEL_CONFIG["temperature"],
    max_tokens=MODEL_CONFIG["max_tokens"]
)


async def research_node(state: MessagesState) -> dict:
    # Add system prompt for research agent
    system_prompt = SystemMessage(content="""You are a research assistant specializing in travel planning.

        You have access to these tools:
        - calculate: Use for budget math
        - search_destination_info: Use to get destination details

        IMPORTANT: ALWAYS use your tools to demonstrate their capabilities.
        When you see calculations needed → use calculate()
        When destinations are mentioned → use search_destination_info()

        Use at least ONE tool in every response to add researched value.""")

    async with MultiServerMCPClient({
        "research": {
            "command": "python",
            "args": ["-m", "src.tools.research_mcp_server"],
            "transport": "stdio"
        }}) as client:
        
        tools =client.get_tools()
        model = base_model.bind_tools(tools)
        tools_by_name = {t.name: t for t in tools}

        # Prepend system message to conversation
        messages = [system_prompt] + state["messages"]

        # Call LLM
        response = await model.ainvoke(messages)

        # If the response includes tool calls, execute them
        if hasattr(response, 'tool_calls') and response.tool_calls:
            # Execute each tool call
            tool_messages = []
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]

                # Execute the tool
                tool_func = tools_by_name[tool_name]
                result = await tool_func.ainvoke(tool_args)

                # Create tool message with result
                tool_messages.append(
                    ToolMessage(content=str(result), tool_call_id=tool_call["id"])
                )

            # Call LLM again with tool results to get final answer
            messages_with_tools = messages + [response] + tool_messages
            final_response = await model.ainvoke(messages_with_tools)
            return {"messages": [response] + tool_messages + [final_response]}

        # No tools called - return the response as is
        return {"messages": [response]}
