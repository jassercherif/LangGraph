import logging
from fastapi import FastAPI
import inngest
import inngest.fast_api
from inngest.experimental import ai
from dotenv import load_dotenv
import uuid
import os
import datetime
import time
from data_loader import load_and_chunk_pdf, embed_texts
from vector_db import QdrantStorage
from custom_types import RAGChunkAndSrc, RAGUpsertResult, RAGSearchResult, RAGQueryResult
from langchain_openai import ChatOpenAI

load_dotenv()

inngest_client = inngest.Inngest(
    app_id="rag_prod_app",
    logger=logging.getLogger("uvicorn"),
    is_production=False,
    serializer=inngest.PydanticSerializer()
)

@inngest_client.create_function(
    fn_id="RAG: Ingest PDF",
    trigger=inngest.TriggerEvent(event="rag/ingest_pdf"),
    throttle=inngest.Throttle(
        count=2, period=datetime.timedelta(minutes=1)
    ),
    rate_limit=inngest.RateLimit(
        limit=1,
        period=datetime.timedelta(hours=4),
        key="event.data.source_id",
    )
)
async def rag_ingest_pdf(ctx: inngest.Context):
    def _load(ctx: inngest.Context) -> RAGChunkAndSrc:
        pdf_path = ctx.event.data["pdf_path"]
        source_id = ctx.event.data.get("source_id", pdf_path)
        chunks = load_and_chunk_pdf(pdf_path)
        return RAGChunkAndSrc(chunk=chunks, source_id=source_id).model_dump()
    
    def _upsert(chunks_and_src: RAGChunkAndSrc) -> RAGUpsertResult:
        chunks = chunks_and_src["chunk"]
        source_id = chunks_and_src["source_id"]
        vectors = embed_texts(chunks)
        ids = [str(uuid.uuid5(uuid.NAMESPACE_URL, f"{source_id}:{i}")) for i in range(len(chunks))]
        payloads = [{"text": chunks[i], "source": source_id} for i in range(len(chunks))]
        QdrantStorage().upsert(ids, vectors, payloads)
        return RAGUpsertResult(ingested=len(chunks)).model_dump()

    chunks_and_src = await ctx.step.run("load-and-chunk", lambda: _load(ctx))
    ingested = await ctx.step.run("embed-and-upsert", lambda: _upsert(chunks_and_src))
    return ingested

@inngest_client.create_function(
    fn_id="RAG: Query",
    trigger=inngest.TriggerEvent(event="rag/query_pdf_ai")
)
async def rag_query_pdf_ai(ctx: inngest.Context):
    def _search(question: str, top_k: int = 5) -> RAGSearchResult:
        query_vector = embed_texts([question])[0]
        store = QdrantStorage()
        found = store.search(query_vector, top_k)
        return RAGSearchResult(contexts=found["contexts"], sources=found["sources"]).model_dump()
    question = ctx.event.data["question"]
    top_k = int(ctx.event.data.get("top_k", 5))
    
    found = await ctx.step.run("embed-and-search", lambda: _search(question, top_k))
    context_block = "\n\n".join(f"- {c}" for c in found["contexts"])
    user_content = (
        "Use the following context to answer the question. \n\n"
        f"Context:\n{context_block}\n\n"
        f"Question: {question}\n"
        "Answer concisely using the context above."
    )
    
    adapter =  ChatOpenAI(
    model="openai/gpt-oss-20b:free",  #qwen/Qwen3-4B:free,  # nex-agi/deepseek-v3.1-nex-n1:free
    temperature=0.2,
    openai_api_key=os.getenv("OPR_KEY"),  # Change environment variable name
    openai_api_base="https://openrouter.ai/api/v1",  # This is the key change
    max_tokens=1024,
    timeout=None,
    max_retries=2,
)
    """ai.OpenAIAdapter(
        model="openai/gpt-oss-20b:free",
        api_key=os.getenv("OPR_KEY"),
        base_url="https://openrouter.ai/api/v1"
        )"""
    def generate_answer(user_content: str) -> str:
      return adapter.invoke([
        {"role": "system", "content": "You answer questions using only the provided context."},
        {"role": "user", "content": user_content}
    ]).content
    """res = await ctx.step.ai.infer(
            "llm-answer",
            adapter=adapter,
            body={
                "max_tokens": 1024,
                "temperature": 0.2,
                "messages": [
                    {"role": "system", "content": "You answer questions using only the provided context."},
                    {"role": "user", "content": user_content}
                ]
            }
        )
"""
    #answer = res["choices"][0]["message"]["content"].strip()
    
    answer = await ctx.step.run(
    "llm-answer",
    lambda: generate_answer(user_content)
)
    return {"answer": answer, "sources": found["sources"], "num_contexts": len(found["contexts"])}

app = FastAPI()


inngest.fast_api.serve(app, inngest_client, [rag_ingest_pdf,rag_query_pdf_ai])