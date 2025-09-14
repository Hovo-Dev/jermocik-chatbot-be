# mock_responder_agent.py

from agents import Agent, Runner, function_tool
from graphrag_client import GraphRAGClient
from csv_file_filter_agent import CSVAgent
from rag.rag_engine import RAGEngine

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

def chart_rag_query(user_input: str) -> str:
    """
    Extract / reason over information extracted from charts.
    """
    rag_engine = RAGEngine()
    context = rag_engine.retrieve_and_build_context(user_input)
    return context


# Wrap them as function_tools so they are usable by the agent
@function_tool
def graph_rag_tool(query: str) -> str:
    return graph_rag_query(query)

@function_tool
def table_query_tool(query: str) -> str:
    return table_query(query)

@function_tool
def chart_rag_tool(query: str) -> str:
    return chart_rag_query(query)


# The responder agent: it has all three tools
def build_responder_agent() -> Agent:
    return Agent(
        name="HybridResponder",
        instructions="""
    You are a responder agent. For each user message, you should call the available tools. graph_rag_tool, table_query_tool, chart_rag_tool 
    are most appropriate to use to fetch information. Then use those tools, gather their responses, and combine into a single answer to the user.
    If uncertain, you may use more than one tool. Always explain which source/tool you're using.
    Use the prior conversation dialogue to generate the next Agent message. Pass the User's request to the tools to retrieve the relevant information.
        """.strip(),
        tools=[graph_rag_tool, table_query_tool, chart_rag_tool],
    )


def run_responder(chat_history: str) -> str:
    """
    Utility to run the agent synchronously (or in your framework’s runner) on a user message.
    """
    agent = build_responder_agent()
    result = Runner.run_sync(agent, chat_history)
    return result.output_text

