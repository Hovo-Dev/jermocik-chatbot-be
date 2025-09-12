"""
End-to-end GraphRAG pipeline:
- Ingest PDFs -> Neo4j using LLM-based KG Builder (auto schema)
- Add metadata to Document/Chunk nodes
- Create vector & full-text indexes
- Run HybridCypher retrieval (vector + full-text + graph traversal)

Docs:
- SimpleKGPipeline (KG Builder)  https://neo4j.com/docs/neo4j-graphrag-python/current/user_guide_kg_builder.html
- RAG user guide & retrievers    https://neo4j.com/docs/neo4j-graphrag-python/current/user_guide_rag.html
- LLM extractor API              https://neo4j.com/docs/neo4j-graphrag-python/current/api.html
"""

import os
import asyncio
from pathlib import Path
from typing import Iterable, Dict
from dotenv import load_dotenv
load_dotenv()  # this loads variables from .env into os.environ


from neo4j import GraphDatabase

# GraphRAG for Python: LLMs, embeddings, KG Builder, indexes, retrievers, RAG wrapper
from neo4j_graphrag.llm import OpenAILLM
from neo4j_graphrag.embeddings import OpenAIEmbeddings
from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline
from neo4j_graphrag.indexes import create_vector_index
from neo4j_graphrag.retrievers import HybridCypherRetriever
from neo4j_graphrag.generation import GraphRAG


# -------------------------
#  CONFIG (env vars are recommended)
# -------------------------
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j+s://0001c33b.databases.neo4j.io")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "JnNafadfa3UDnUAv2rHKnjGt7ldQCD18apZsfhzWC1kxWYJRU")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

# Choose your LLM & embedding provider per GraphRAG docs
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-large")
EMBED_DIM = int(os.getenv("EMBED_DIM", "3072"))  # 3072 for text-embedding-3-large; 1536 for -small

# Index names
VEC_INDEX = os.getenv("VEC_INDEX", "chunk_embeddings")
FT_INDEX = os.getenv("FT_INDEX", "chunk_fulltext")

OPENAI_KEY = os.getenv("OPENAI_API_KEY")

# -------------------------
#  NEO4J DRIVER
# -------------------------
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# -------------------------
#  LLM + EMBEDDER
# -------------------------
llm = OpenAILLM(model_name=OPENAI_MODEL, model_params={"temperature": 0, "response_format": {"type": "json_object"}},)
embedder = OpenAIEmbeddings(model=EMBED_MODEL)


# -------------------------
#  1) INGEST PDFs -> KG
#     (automatic schema extraction by default)
#     Docs: SimpleKGPipeline
# -------------------------
async def ingest_pdfs(pdf_paths: Iterable[str]) -> None:
    """
    Uses the Knowledge Graph Builder (SimpleKGPipeline) to:
    - load PDFs
    - chunk text
    - (optionally) embed chunks
    - extract entities & relations with an LLM
    - write lexical graph (Document/Chunk/NEXT_CHUNK) + entity graph to Neo4j
    """
    kg = SimpleKGPipeline(
        llm=llm,
        driver=driver,
        embedder=embedder,      # stores embeddings on Chunk nodes for RAG
        from_pdf=True,          # parse PDFs directly
        neo4j_database=NEO4J_DATABASE,
        schema="FREE"           # default => automatic schema inference (guided)
        # create_lexical_graph=True (default)
    )


    for p in pdf_paths:
        abs_path = str(Path(p).resolve())
        print(f"Ingesting: {abs_path}")
        await kg.run_async(file_path=abs_path)
        print(f"Completed: {abs_path}")


# -------------------------
#  2) ADD METADATA
#     (Neo4j is a property-graph; attach arbitrary properties)
# -------------------------
def add_document_metadata(path: str, meta: Dict) -> None:
    """
    Adds/updates properties on the Document node created by the lexical graph
    (Document has a stable 'path' property that equals the absolute file path).
    """
    with driver.session(database=NEO4J_DATABASE) as s:
        s.run("""
        MATCH (d:Document {path: $path})
        SET d += $meta
        """, path=str(Path(path).resolve()), meta=meta)


def tag_first_chunks(path: str, upto_index: int, section: str) -> None:
    """
    Example: tag the first N chunks as 'prepared_remarks' or similar.
    """
    with driver.session(database=NEO4J_DATABASE) as s:
        s.run("""
        MATCH (d:Document {path: $path})-[:HAS_CHUNK]->(c:Chunk)
        WHERE c.index < $upto
        SET c.section = $section
        """, path=str(Path(path).resolve()), upto=upto_index, section=section)


# -------------------------
#  3) INDEXES (vector + full-text)
#     Docs: RAG user guide + index helpers
# -------------------------
def ensure_fulltext_index() -> None:
    """
    Creates a Neo4j full-text index for Chunk.text if it doesn't exist.
    You only need to run this once per DB.
    """
    cypher = f"""
    CALL db.index.fulltext.createNodeIndex('{FT_INDEX}', ['Chunk'], ['text'])
    """
    with driver.session(database=NEO4J_DATABASE) as s:
        try:
            s.run(cypher)
            print(f"Created full-text index: {FT_INDEX}")
        except Exception as e:
            # Likely already exists; ignore or log as needed
            print(f"(Note) Full-text index may already exist: {e}")


def ensure_vector_index() -> None:
    """
    Creates a vector index over Chunk.embedding (written by the KG builder
    when an embedder is provided).
    """
    create_vector_index(
        driver,
        name=VEC_INDEX,
        label="Chunk",
        embedding_property="embedding",
        dimensions=EMBED_DIM,
        similarity_fn="cosine"
    )
    print(f"Ensured vector index: {VEC_INDEX}")


# -------------------------
#  4) RETRIEVAL (HybridCypher = vector + full-text + traversal)
#     Docs: Hybrid retrievers + traversal patterns
# -------------------------
def ask(question: str, top_k: int = 6) -> str:
    """
    Runs hybrid retrieval:
    - ANN vector search on embeddings
    - full-text search on Chunk.text
    - then expands context via NEXT_CHUNK hops
    Passes results to LLM for answer generation (GraphRAG wrapper).
    """
    retriever = HybridCypherRetriever(
        driver,
        vector_index=VEC_INDEX,
        fulltext_index=FT_INDEX,
        embedder=embedder,
        # Expand around the hit to include neighbors in context:
        retrieval_query="""
          MATCH (node)-[:NEXT_CHUNK*0..2]->(ctx:Chunk)
          RETURN node AS chunk, score, collect(ctx) AS more
        """,
        database=NEO4J_DATABASE
    )

    rag = GraphRAG(retriever=retriever, llm=llm)
    result = rag.search(query_text=question, retriever_config={"top_k": top_k})
    return result.answer


# -------------------------
#  MAIN (example)
# -------------------------
if __name__ == "__main__":
    pdfs = [
        "prompts/pdfs/2022_Q3_Earnings_Transcript.pdf",
        "prompts/pdfs/2023-q4-earnings-transcript.pdf",
        # add more PDFs here...
    ]

    # 1) Ingest PDFs -> KG (auto schema; creates lexical + entity graph)
    asyncio.run(ingest_pdfs(pdfs))

    # 2) Add metadata examples
    add_document_metadata(
        "2025-q1-earnings-transcript.pdf",
        {"doc_type": "transcript", "quarter": "Q1-2025", "published_at": "2025-04-24"}
    )
    tag_first_chunks("prompts/pdfs/2022_Q3_Earnings_Transcript.pdf", upto_index=5, section="prepared_remarks")

    # 3) Set up indexes for retrieval
    ensure_fulltext_index()
    ensure_vector_index()

    # 4) Ask questions
    q1 = "were the q4 additions higher than q3?"
    print("\nQ:", q1)
    print("A:", ask(q1, top_k=6))

    # q2 = "Summarize commentary about AI agents mentioned in the latest call."
    # print("\nQ:", q2)
    # print("A:", ask(q2, top_k=6))
