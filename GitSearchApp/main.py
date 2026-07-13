import os
import requests
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_cohere import CohereEmbeddings
from langchain_astradb import AstraDBVectorStore

from langgraph.prebuilt import create_react_agent
from langchain_core.tools.retriever import create_retriever_tool
from langsmith import Client
from github import fetch_github_issues
from note import note_tool

load_dotenv()

def connect_to_vstore():
    Embedding_MODEL = os.getenv("Embedding_MODEL")

    embeddings = CohereEmbeddings(
        model=Embedding_MODEL, 
        cohere_api_key=os.getenv("CH_KEY"), 
    )
    ASTRA_DB_ENDPOINT = os.getenv("ASTRA_DB_ENDPOINT")
    ASTRA_DB_APPLICATION_TOKEN = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
    desired_namespace = os.getenv("ASTRA_DB_KEYSPACE")

    if desired_namespace:
        ASTRA_DB_KEYSPACE = desired_namespace
    else:
        ASTRA_DB_KEYSPACE = None

    vstore = AstraDBVectorStore(
        embedding=embeddings,
        collection_name="github_issues",
        api_endpoint=ASTRA_DB_ENDPOINT,
        token=ASTRA_DB_APPLICATION_TOKEN,
        namespace=ASTRA_DB_KEYSPACE
    )
    return vstore

vstore = connect_to_vstore()
add_to_vectorstore = input("Do you want to update the issues? (y/N): ").lower() in [
    "y",
    "yes"
    ]
if add_to_vectorstore:
    owner = "jassercherif"
    repo = "CodeAssistant"
    issues = fetch_github_issues(owner, repo)
    try:
        vstore.delete_collection()
    except:
        pass
    
    vstore = connect_to_vstore()
    print('Issues: ',issues)
    vstore.add_documents(issues)

    #results = vstore.similarity_search("flash messages", k=3)
    #for res in results:
    #   print(f"* {res.page_content} {res.metadata}")
    
retriever = vstore.as_retriever(search_kwargs={"k": 3})
retriever_tool = create_retriever_tool(
    retriever,
    "github_search", 
    "Search for information about github issues. For any questions about github issues, you must use this tool!"
    )

client = Client(api_key=os.getenv("LANGSMITH_API_KEY"))
prompt = client.pull_prompt("hwchase17/openai-functions-agent")
llm = ChatOpenAI(
        model="openai/gpt-oss-20b:free",  #qwen/Qwen3-4B:free,  # nex-agi/deepseek-v3.1-nex-n1:free
        temperature=0.2,
        openai_api_key=os.getenv("OPR_KEY"),  # Change environment variable name
        openai_api_base="https://openrouter.ai/api/v1",  # This is the key change
        max_tokens=1024,
        timeout=None,
        max_retries=2,
    )
tools = [retriever_tool, note_tool]
agent = create_react_agent(
    model=llm,
    tools=tools,
    #prompt=prompt,
    #verbose=True 
    )
while (question := input("Ask a question about github issues (q to quit): ")) != "q":
    result = agent.invoke({
        "messages": [("human", question)]
    })

    print("\nANSWER:\n", result["messages"][-1].content)