import os
import certifi
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

# ── SSL certs (needed for some environments) ──────────────────────────────────
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()


def get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL is missing. Please set it in your .env file.")
    if "sslmode=" not in url:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}sslmode=require"
    return url


_groq_api_key = os.getenv("GROQ_API_KEY")
if not _groq_api_key:
    raise ValueError("GROQ_API_KEY is missing. Please add it to your .env file.")

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=_groq_api_key,
)
