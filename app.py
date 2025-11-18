import os
import time
from dotenv import load_dotenv

from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")  # ensure no typo

if not OPENAI_API_KEY or not PINECONE_API_KEY:
    raise RuntimeError("Set OPENAI_API_KEY and PINECONE_API_KEY in your environment or .env")

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY

# ---- load and split docs ----
loader = DirectoryLoader(path="./data/new_articles/", glob="*.txt", loader_cls=TextLoader)
raw_docs = loader.load()

text_splitter = RecursiveCharacterTextSplitter(separators=["\n\n", "\n"], chunk_size=1000, chunk_overlap=20)
documents = text_splitter.split_documents(raw_docs)
print(f"Loaded {len(documents)} document chunks")

# ---- embedding model ----
embedding = OpenAIEmbeddings(api_key=OPENAI_API_KEY, model="text-embedding-3-small")

# determine embedding dimension from a sample
sample_vec = embedding.embed_query("sample")
EMBED_DIM = len(sample_vec)
print("Detected embedding dimension:", EMBED_DIM)

# ---- pinecone client ----
pc = Pinecone(api_key=PINECONE_API_KEY)
requested_index_name = "tester-index"        # your preferred name
index_name = requested_index_name

# check existing indexes
try:
    existing = pc.list_indexes().names()
except Exception as e:
    print("Unable to list indexes:", e)
    existing = []

print("Existing indexes:", existing)

# if index exists, check dimension mismatch
create_new = False
if index_name in existing:
    print(f"Index '{index_name}' exists — checking dimension...")
    info = pc.describe_index(index_name)
    # safe approach: compare by attempting to read a property; if not present, rely on error later
    # Many Pinecone SDK versions include dimension in describe_index() result:
    idx_dim = None
    if hasattr(info, "dimension"):
        idx_dim = info.dimension
    else:
        # fallback: read status or metadata if available
        try:
            # info may be dict-like
            idx_dim = info.get("dimension") if isinstance(info, dict) else None
        except Exception:
            idx_dim = None

    print("Index metadata (describe_index):", info)
    if idx_dim is not None:
        print(f"Index dimension = {idx_dim}")
        if idx_dim != EMBED_DIM:
            print(f"Dimension mismatch: index={idx_dim} vs embeddings={EMBED_DIM}")
            # choose to create a new index (safe)
            index_name = f"{requested_index_name}-v{EMB_ED_DIM}" if False else f"{requested_index_name}-v2"
            create_new = True
    else:
        # if we couldn't read dimension reliably, still create new index to be safe
        print("Could not read index dimension reliably; will create a new index to avoid mismatch.")
        index_name = f"{requested_index_name}-v2"
        create_new = True
else:
    # index doesn't exist — create with correct dim
    create_new = True

# create the new index if required
if create_new:
    print(f"Creating new index '{index_name}' with dimension={EMBED_DIM} ...")
    pc.create_index(
        name=index_name,
        dimension=EMBED_DIM,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1"),
    )

# wait until index ready
print("Waiting for index to become ready...")
while True:
    info = pc.describe_index(index_name)
    ready = info.status.get("ready", False) if hasattr(info, "status") else info.get("status", {}).get("ready", False)
    print("Index ready:", ready)
    if ready:
        break
    time.sleep(1)

index = pc.Index(index_name)
print("Using index:", index_name)

# ---- embed documents and upsert ----
# Prepare texts and ids
texts = [d.page_content for d in documents]
ids = [f"doc-{i}" for i in range(len(texts))]

# embed in batches (embedding.embed_documents accepts list)
print("Embedding documents in batches...")
vectors = embedding.embed_documents(texts)  # returns list of lists (vectors)
# build upsert items as (id, vector, metadata)
to_upsert = []
for _id, vec, doc in zip(ids, vectors, documents):
    meta = doc.metadata if hasattr(doc, "metadata") else {}
    to_upsert.append({"id": _id, "values": vec, "metadata": meta})

# upsert to pinecone
print(f"Upserting {len(to_upsert)} vectors into index '{index_name}' ...")
# use the index client directly
index.upsert(vectors=to_upsert)

print("Upsert complete.")

# ---- create LangChain vectorstore ----
docsearch = PineconeVectorStore.from_documents(
    documents=documents,
    embedding=embedding,
    index_name=index_name,
    pinecone_api_key=PINECONE_API_KEY,
)

print("Vector store ready. Sample search:")
results = docsearch.similarity_search("was bihari rejected from reality shows ?", top_k=2)
print(results)
