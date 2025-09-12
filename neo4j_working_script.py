"""
Neo4j Working Script - Database Population and Querying
Uses neo4j package and Knowledge Graph Builder to populate Neo4j and perform queries.

This script demonstrates:
1. Connecting to Neo4j database
2. Populating the graph with sample data
3. Using Knowledge Graph Builder for document ingestion
4. Running various Cypher queries
5. RAG-based question answering
"""

import os
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Neo4j imports
from neo4j import GraphDatabase
from neo4j_graphrag.types import RetrieverResultItem
from neo4j_graphrag.llm import OpenAILLM
from neo4j_graphrag.embeddings import OpenAIEmbeddings
from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline
from neo4j_graphrag.indexes import create_vector_index
from neo4j_graphrag.retrievers import VectorCypherRetriever
from neo4j_graphrag.generation import GraphRAG

# Load environment variables
load_dotenv()


def log_info(message: str) -> None:
    """Log info messages with emoji indicators."""
    print(f"ℹ️ {message}")


def log_success(message: str) -> None:
    """Log success messages with checkmark."""
    print(f"✅ {message}")


def log_error(message: str) -> None:
    """Log error messages with X mark."""
    print(f"❌ {message}")


def log_warning(message: str) -> None:
    """Log warning messages with warning sign."""
    print(f"⚠️ {message}")


def log_separator(length: int = 80) -> None:
    """Print a separator line."""
    print("=" * length)


def log_section_header(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{title}")
    log_separator()


def format_rag_answer(answer: str) -> None:
    """Format and display RAG answer."""
    log_section_header("🧠 ANSWER")
    print(answer)


def format_context_chunks(retriever_result, top_k: int) -> None:
    """Format and display context chunks with entities and edges."""
    log_section_header("📚 CONTEXT CHUNKS")
    
    for i, item in enumerate(retriever_result.items, 1):
        metadata = item.metadata or {}
        entities = metadata.get("entities", [])
        edges = metadata.get("entity_edges", [])

        print(f"\n=== CHUNK {i}/{top_k} ===")
        print(f"Chunk ID     : {metadata.get('chunk_id')}")
        print(f"Doc Title    : {metadata.get('doc_title')}")
        print(f"Chunk Index  : {metadata.get('chunk_index')}")
        
        similarity = metadata.get('similarity')
        if isinstance(similarity, (int, float)):
            print(f"Similarity   : {similarity:.6f}")
        else:
            print(f"Similarity   : {similarity}")
        
        print("-" * 80)
        print(item.content.strip())
        print("-" * 80)

        # Display entities
        print("🧩 ENTITIES:")
        for entity in entities:
            label_str = ",".join(entity.get("labels", []))
            print(f" • {entity.get('name')}  [{label_str}]  id={entity.get('id')}")

        # Display edges
        entity_by_id = {e["id"]: e for e in entities}
        print("\n🔗 EDGES (among entities in this chunk):")
        
        if not edges:
            print(" (none)")
        else:
            for edge in edges:
                entity_a = entity_by_id.get(edge["a"])
                entity_b = entity_by_id.get(edge["b"])
                if entity_a and entity_b:
                    props_str = f"(props: {edge.get('props')})" if edge.get('props') else ""
                    print(f" • {entity_a.get('name')}  -[{edge['type']}]->  {entity_b.get('name')}  {props_str}")


class Neo4jClient:
    """Neo4j client for graph database operations and RAG queries."""
    
    def __init__(self):
        """Initialize Neo4j client with configuration."""
        self._load_config()
        self._initialize_components()
    
    def _load_config(self) -> None:
        """Load configuration from environment variables."""
        # Neo4j Configuration
        self.neo4j_uri = os.getenv("NEO4J_URI", "neo4j+s://localhost:7687")
        self.neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
        self.neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")
        
        # OpenAI Configuration
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o")
        self.embed_model = os.getenv("EMBED_MODEL", "text-embedding-3-large")
        self.embed_dim = int(os.getenv("EMBED_DIM", "3072"))
        
        # Index names
        self.vector_index = "chunk_embeddings"
    
    def _initialize_components(self) -> None:
        """Initialize Neo4j driver and AI components."""
        # Initialize driver
        self.driver = GraphDatabase.driver(
            self.neo4j_uri, 
            auth=(self.neo4j_user, self.neo4j_password)
        )
        
        # Initialize LLM components
        self.llm_json = OpenAILLM(
            model_name=self.openai_model,
            model_params={
                "temperature": 0,
                "response_format": {"type": "json_object"}
            }
        )
        self.llm = OpenAILLM(
            model_name=self.openai_model,
            model_params={"temperature": 0}
        )
        self.embedder = OpenAIEmbeddings(model=self.embed_model)
    
    def test_connection(self) -> bool:
        """Test Neo4j database connection."""
        try:
            with self.driver.session(database=self.neo4j_database) as session:
                result = session.run("RETURN 1 as test")
                record = result.single()
                log_success(f"Neo4j connection successful: {record['test']}")
                return True
        except Exception as e:
            log_error(f"Neo4j connection failed: {e}")
            return False
    
    def clear_database(self) -> None:
        """Clear all nodes and relationships in the database."""
        with self.driver.session(database=self.neo4j_database) as session:
            session.run("MATCH (n) DETACH DELETE n")
            log_info("Database cleared")
    
    def delete_all_data(self) -> None:
        """Delete all data from Neo4j database."""
        with self.driver.session(database=self.neo4j_database) as session:
            session.run("MATCH (n) DETACH DELETE n")
            log_info("All data deleted from Neo4j database")
    
    async def ingest_documents(self, pdf_paths: List[str]) -> None:
        """Ingest PDF documents using Knowledge Graph Builder."""
        if not pdf_paths:
            log_warning("No PDF paths provided for ingestion")
            return
        
        kg_pipeline = SimpleKGPipeline(
            llm=self.llm_json,
            driver=self.driver,
            embedder=self.embedder,
            from_pdf=True,
            neo4j_database=self.neo4j_database,
            schema="FREE"
        )
        
        for pdf_path in pdf_paths:
            if Path(pdf_path).exists():
                abs_path = str(Path(pdf_path).resolve())
                log_info(f"Ingesting: {abs_path}")
                try:
                    await kg_pipeline.run_async(file_path=abs_path)
                    log_success(f"Completed: {abs_path}")
                except Exception as e:
                    log_error(f"Failed to ingest {abs_path}: {e}")
            else:
                log_warning(f"File not found: {pdf_path}")
    
    def create_indexes(self) -> None:
        """Create vector and full-text indexes."""
        try:
            create_vector_index(
                self.driver,
                name=self.vector_index,
                label="Chunk",
                embedding_property="embedding",
                dimensions=self.embed_dim,
                similarity_fn="cosine"
            )
            log_success(f"Created vector index: {self.vector_index}")
        except Exception as e:
            log_warning(f"Vector index may already exist: {e}")
    
    def _build_retrieval_query(self) -> str:
        """Build the Cypher query for retrieval."""
        return """
        // Collect entities connected to the matched chunk
        OPTIONAL MATCH (e)-[:FROM_CHUNK]->(node)
        // Collect inter-entity edges among those entities (both directions)
        WITH node, score, collect(DISTINCT e) AS es
        OPTIONAL MATCH (e1)-[er]-(e2)
        WHERE e1 IN es AND e2 IN es AND id(e1) < id(e2)
        WITH node, score, es,
             collect(DISTINCT {type:type(er), a:elementId(e1), b:elementId(e2), props:properties(er)}) AS entity_edges
        // Shape entities as plain maps (no raw nodes)
        WITH node, score, entity_edges,
             [e IN es |
               { id: elementId(e),
                 labels: labels(e),
                 name: coalesce(e.name, e.title, e.value, e.text, toString(elementId(e))),
                 props: properties(e)
               }
             ] AS entities
        // Bring back the document title when available
        OPTIONAL MATCH (node)-[:FROM_DOCUMENT]->(d)
        RETURN
          elementId(node)                                   AS chunk_id,
          coalesce(node.index, -1)                          AS chunk_index,
          coalesce(node.text, node.content, '')             AS chunk_text,
          score                                             AS similarity,
          d.title                                           AS doc_title,
          entities,
          entity_edges
        """
    
    def _format_retriever_result(self, record: Dict[str, Any]) -> RetrieverResultItem:
        """Format database record into RetrieverResultItem."""
        return RetrieverResultItem(
            content=record.get("chunk_text") or "",
            metadata={
                "chunk_id": record.get("chunk_id"),
                "chunk_index": record.get("chunk_index"),
                "similarity": record.get("similarity"),
                "doc_title": record.get("doc_title"),
                "entities": record.get("entities") or [],
                "entity_edges": record.get("entity_edges") or [],
            },
        )
    
    def ask_question(self, question: str, top_k: int = 5) -> str:
        """Ask a question using RAG and display detailed results."""
        try:
            retriever = VectorCypherRetriever(
                driver=self.driver,
                index_name=self.vector_index,
                retrieval_query=self._build_retrieval_query(),
                embedder=self.embedder,
                result_formatter=self._format_retriever_result,
                neo4j_database=self.neo4j_database,
            )

            rag = GraphRAG(retriever=retriever, llm=self.llm)
            result = rag.search(
                query_text=question, 
                retriever_config={"top_k": top_k}, 
                return_context=True
            )

            # Display formatted results
            format_rag_answer(result.answer)
            format_context_chunks(result.retriever_result, top_k)

            return result.answer
        except Exception as e:
            error_msg = f"RAG query failed: {e}"
            log_error(error_msg)
            return error_msg
    
    def close(self) -> None:
        """Close the Neo4j driver."""
        self.driver.close()
        log_info("Neo4j connection closed")


async def main():
    """Main function demonstrating the Neo4j working script."""
    log_info("Starting Neo4j Working Script")
    log_separator(50)
    
    # Initialize the client
    client = Neo4jClient()
    
    # Test connection
    if not client.test_connection():
        return

    # Define PDF files for ingestion
    pdf_files = [
        "prompts/pdfs/2022_Q3_Earnings_Transcript.pdf",
        "prompts/pdfs/2023-q4-earnings-transcript.pdf",
        "prompts/pdfs/2023-q2-earnings-transcript.pdf"
    ]

    # Uncomment to clear data and ingest documents
    # client.delete_all_data()
    # await client.ingest_documents(pdf_files)
    # client.create_indexes()

    # RAG-based questions
    questions = [
        "where was lamda demonstrated?",
        # "Which hardware partners were highlighted and for what integrations?",
        # "Summarize the AI in Ads community across the three quarters."
    ]

    for question in questions:
        print(f"\n❓ Question: {question}")
        answer = client.ask_question(question)
        print(f"\n💡 Final Answer: {answer}")

    log_success("Script completed successfully!")
    client.close()


if __name__ == "__main__":
    asyncio.run(main())