# mock_responder_agent.py

from agents import Agent, Runner, function_tool, MessageOutputItem, ToolCallItem, ToolCallOutputItem, HandoffOutputItem
from agents import ItemHelpers
from rag.graphrag_client import GraphRAGClient
from etl.csv_file_filter_agent import CSVAgent
from rag.rag_engine import RAGEngine
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)

def log_result(result):
    """Logs the result of an agent's response."""
    for new_item in result.new_items:
        agent_name = new_item.agent.name

        if isinstance(new_item, MessageOutputItem):
            message_text = ItemHelpers.text_message_output(new_item)
            logging.info(f"====== {agent_name}: {message_text} ======")

        elif isinstance(new_item, ToolCallItem):
            call_data = new_item.raw_item.model_dump()
            tool_name = call_data.get("name") or call_data.get("tool") or "UnknownTool"
            arguments = call_data.get("arguments") or call_data.get("query") or {}
            logging.info(
                f"====== {agent_name}: Calling tool '{tool_name}' "
                f"with arguments: {arguments} ======"
            )

        elif isinstance(new_item, ToolCallOutputItem):
            logging.info(f"====== {agent_name}: Tool call output: {new_item.output} ======")

        elif isinstance(new_item, HandoffOutputItem):
            logging.info(
                f"====== Handed off from {new_item.source_agent.name}"
                f"to {new_item.target_agent.name} ======"
            )

        else:
            logging.info(
                f"====== {agent_name}: Skipping item: {new_item.__class__.__name__} ======"
            )

# Assume these are your mock tool functions you already implemented
def graph_rag_query(user_input: str) -> str:
    """
    Use GraphRAG to fetch / reason over your graph‐based knowledge.
    """
    client = GraphRAGClient()
    return client.ask_question(user_input)

def table_query(user_input: str) -> str:
    """
    Query structured tables based on user input.
    """
    csv_agent = CSVAgent()
    return csv_agent.run(user_input)


# Wrap them as function_tools so they are usable by the agent
@function_tool
def graph_rag_tool(query: str) -> str:
    return graph_rag_query(query)

@function_tool
def table_query_tool(query: str) -> str:
    return table_query(query)


# The responder agent: it has all three tools
def build_responder_agent(context: str) -> Agent:
    instructions = """
    You are a responder agent. For each user message, you should call ALL the available tools. graph_rag_tool, table_query_tool 
    are most appropriate to use to fetch information. Then use those tools, gather their responses, and combine into a single answer to the user.
    If uncertain, you may use more than one tool. Always explain which source/tool you're using.
    Use the prior conversation dialogue to generate the next Agent message. Pass the User's request to the tools to retrieve the relevant information.
    ATTENTION; ALWAYS USE ALL THE TOOLS. AGGREGATE THE RESPONSES FROM THE TOOLS.
    ATTENTION; PAY ATTENTION TO THE FOLLOWING CONTEXT AND ALWAYS ANSWER IF RELEVANT TO THE USER'S REQUEST: 
    {context}.
    """.strip().format(context=context)

    logging.info(f"Instructions: {instructions}")

    return Agent(
        name="HybridResponder",
        instructions=instructions,
        tools=[graph_rag_tool, table_query_tool],
    )


def run_responder(chat_history: str, retrieved_context: str) -> str:
    """
    Utility to run the agent synchronously (or in your framework's runner) on a user message.
    """
    import asyncio
    
    agent = build_responder_agent(context=retrieved_context)

    result = asyncio.run(Runner.run(agent, chat_history))

    return result.final_output
