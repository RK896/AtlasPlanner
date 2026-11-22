from langgraph.graph import MessagesState


class TravelState(MessagesState):
    """Shared state for one conversation.

    messages:   full conversation (user turns, specialist reports, planner replies);
                appended to via the add_messages reducer from MessagesState
    visited:    specialists already consulted for the current user turn
                (reset by the caller at the start of every turn)
    next_agent: where the planner decided to go next
    task:       the planner's instruction for that specialist
    """

    visited: list[str]
    next_agent: str
    task: str
