from typing import List, Optional, Dict, Any, Union,TypedDict
import os
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START,END
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file


llm = ChatOpenAI(
    model="qwen/qwen3.6-plus-preview:free",  #qwen/Qwen3-4B:free,  # nex-agi/deepseek-v3.1-nex-n1:free
    temperature=0,
    openai_api_key=os.getenv("OPR_KEY"),  # Change environment variable name
    openai_api_base="https://openrouter.ai/api/v1",  # This is the key change
    max_tokens=2048,
    timeout=None,
    max_retries=2,
)

class AgentState(TypedDict):
    messages: List[Union[HumanMessage, AIMessage]]

def process(state: AgentState) -> AgentState:
    """This node will solve the request you input"""
    response = llm.invoke(state['messages'])
    
    state['messages'].append(AIMessage(content=response.content))
    print(f"Agent: {response.content}")
    return state

graph = StateGraph(AgentState)
graph.add_node("process", process)
graph.add_edge(START, "process")
graph.add_edge("process", END)
app = graph.compile()

conversation_history = []

user_input = input("You: ")
while user_input.lower() != "exit":
    conversation_history.append(HumanMessage(content=user_input))

    result = app.invoke({"messages": conversation_history})
    conversation_history = result['messages']  # Update conversation history with the latest messages
    user_input = input("You: ")