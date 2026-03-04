from langgraph.graph import MessagesState
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, ToolMessage
from src.utils.config import API_KEY, MODEL_CONFIG
from langchain_mcp_adapters.client import MultiServerMCPClient




base_model = ChatAnthropic(
    api_key = API_KEY,
    model = MODEL_CONFIG["model"],
    temperature=MODEL_CONFIG["temperature"],
    max_tokens=MODEL_CONFIG["max_tokens"]
)
model = base_model.bind_tools([search_roundtrip, search_oneway])

async def flights_node(state:MessagesState) -> dict:
    system_prompt = SystemMessage(content="""You a are a flight finding specialist
                                  You have access to these tools:
                                  - search_roundtrip: use to find flights for a roundtrip
                                  - search_oneway: use to find one way flights
                                  """)

    async with MultiServerMCPClient({
        "travel":{
            "command": "python",
            "args": ["m", "src.tools.flights_mcp_server"]
        }
    }) as client:
        messages = [system_prompt] + state["messages"]

        tools =client.get_tools()
        model = base_model.bind_tools(tools)
        tools_by_name = tools_by_name = {t.name: t for t in tools}


        response = await model.ainvoke(messages)

        if hasattr(response, 'tool_calls') and response.tool_calls:
            # Execute each tool call
            tool_messages = []
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]

                # Execute the tool
                tool_func = tools_by_name[tool_name]
                result = tool_func.invoke(tool_args)

                # Create tool message with result
                tool_messages.append(
                    ToolMessage(content=str(result), tool_call_id=tool_call["id"])
                )

            # Call LLM again with tool results to get final answer
            messages_with_tools = messages + [response] + tool_messages
            final_response = model.invoke(messages_with_tools)
            return {"messages": [response] + tool_messages + [final_response]}

        # No tools called - return the response as is
        return {"messages": [response]}
