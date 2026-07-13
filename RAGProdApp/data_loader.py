from langchain_cohere import CohereEmbeddings
from llama_index.readers.file import PDFReader
from llama_index.core.node_parser import SentenceSplitter
from dotenv import load_dotenv
import os
import time

load_dotenv()

Embedding_MODEL = os.getenv("Embedding_MODEL")
Embedding_DIM = int(os.getenv("Embedding_DIM"))
client = CohereEmbeddings(
    model=Embedding_MODEL, 
    cohere_api_key=os.getenv("CH_KEY"), 
    #dimensions=Embedding_DIM
    )

splitter = SentenceSplitter(chunk_size=500, chunk_overlap=100)

def load_and_chunk_pdf(path: str):
    docs = PDFReader().load_data(file=path)
    text = [d.text for d in docs if getattr(d, "text", None)]
    chunks = []
    for t in text:
        chunks.extend(splitter.split_text(t))
    return chunks

def embed_texts(texts: list[str]) -> list[list[float]]:
    batch_size = 10
    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]

        embeddings = client.embed_documents(batch)
        all_embeddings.extend(embeddings)

        time.sleep(0.3)  # avoid rate limits

    return all_embeddings