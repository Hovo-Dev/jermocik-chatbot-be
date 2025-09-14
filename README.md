# Awesome Jermocik Chatbot

An intelligent chatbot system that combines Django REST API, RAG (Retrieval-Augmented Generation), and GraphRAG for advanced document processing and conversational AI. The system can process PDF documents, extract structured data, and provide intelligent responses based on the processed content.

## 🏗️ Architecture

This project consists of several key components:

- **Django REST API**: Core web application with user authentication and chat functionality
- **RAG Engine**: Vector-based document retrieval using pgvector and OpenAI embeddings
- **GraphRAG**: Graph-based knowledge retrieval using Neo4j
- **ETL Pipeline**: PDF document processing with VLM (Vision-Language Model) extraction
- **Multi-Agent System**: Hybrid responder combining multiple data sources

## 🚀 Quick Start with Docker

### Prerequisites

- Docker and Docker Compose
- OpenAI API key
- At least 8GB RAM available for Docker

### 1. Environment Setup

```bash
# Copy environment template
cp env.example .env

# Edit .env file with your configuration
# IMPORTANT: Set your OPENAI_API_KEY
```

### 2. Start the Application

#### Development Mode
```bash
# Start all services in development mode
make dev

# Or manually:
docker compose -f docker-compose.dev.yml up --build
```

#### Production Mode
```bash
# Start all services in production mode
make prod

# Or manually:
docker compose up --build -d
```

### 3. Initialize the Database

```bash
# Run migrations
make migrate

# Create a superuser
make superuser
```

### 4. Access the Services

- **API**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin
- **pgAdmin**: http://localhost:5050 (admin@admin.com / admin)
- **Neo4j**: bolt://localhost:7687 (neo4j / password)

## 📋 Available Commands

The project includes a Makefile with useful commands:

```bash
make help       # Show all available commands
make dev        # Start development environment  
make prod       # Start production environment
make build      # Build Docker containers
make down       # Stop all services
make clean      # Stop and remove volumes
make migrate    # Run database migrations
make logs       # Show logs
make shell      # Open Django shell
make superuser  # Create superuser
make db-shell   # Connect to database
```

## 📊 ETL Pipeline & Document Ingestion

### Running the ETL Pipeline

The ETL pipeline processes PDF documents and extracts structured data using Vision-Language Models:

```bash
# Process PDFs in the etl/input directory
docker compose exec web uv run python etl/main.py

# Custom input/output directories
docker compose exec web uv run python etl/main.py --input /path/to/pdfs --output /path/to/results

# Use different VLM model
docker compose exec web uv run python etl/main.py --model gpt-4o-mini
```

### ETL Pipeline Features

- **PDF Processing**: Converts PDF pages to images for VLM analysis
- **Table Extraction**: Extracts structured tables and saves as CSV
- **Chart Analysis**: Analyzes charts and figures with key insights
- **Vector Embeddings**: Creates embeddings for RAG retrieval
- **Batch Processing**: Handles multiple PDFs efficiently

### Input Data

Place your PDF documents in the `etl/input/` directory. The pipeline will:

1. Process each PDF page-by-page
2. Extract tables and convert to CSV format
3. Analyze charts and generate descriptions
4. Create vector embeddings for retrieved context
5. Store structured data in PostgreSQL and Neo4j

### RAG Data Ingestion API

After placing PDFs in the `etl/input/` directory, use these API endpoints to ingest data:

#### GraphRAG Ingestion (Recommended)
```bash
# Ingest documents into GraphRAG (Neo4j) - No authentication required
curl -X POST http://localhost:8000/api/v1/rag/documents/ingest/graphrag/ \
  -H "Content-Type: application/json"
```

This endpoint will:
- Test Neo4j connection
- Process all PDF files from `etl/input/` directory
- Create graph relationships and indexes
- Enable graph-based retrieval for chat responses

**Note**: You only need to run GraphRAG ingestion. The structured ETL data ingestion is handled automatically during the pipeline processing.

## 💬 Chat & RAG System

### Chat API Endpoints

```bash
# Create a new conversation
POST /api/v1/chat/conversations/

# Send a message
POST /api/v1/chat/conversations/{id}/messages/
{
  "content": "What were the key financial metrics in Q1 2024?"
}

# Get conversation history
GET /api/v1/chat/conversations/{id}/messages/
```

### RAG Configuration

The system uses multiple retrieval methods:

- **Vector RAG**: Semantic search using pgvector and OpenAI embeddings
- **GraphRAG**: Graph-based retrieval using Neo4j relationships
- **Table Query**: Direct CSV data querying

Configure RAG settings in your `.env` file:

```env
RAG_EMBEDDING_MODEL=text-embedding-3-small
RAG_VECTOR_DIMENSION=1536
RAG_TOP_K_RESULTS=5
RAG_SIMILARITY_THRESHOLD=0.6
```

## 🗄️ Database Configuration

### PostgreSQL with pgvector

The system uses PostgreSQL with the pgvector extension for vector storage:

```sql
-- Vector similarity search
SELECT content, 1 - (embedding <=> query_vector) as similarity 
FROM rag_documentchunk 
WHERE 1 - (embedding <=> query_vector) > 0.6
ORDER BY embedding <=> query_vector 
LIMIT 5;
```

### Neo4j GraphRAG

Neo4j stores document relationships and enables graph-based retrieval:

- Nodes: Documents, chunks, entities
- Relationships: Contains, mentions, relates_to
- Queries: Cypher-based graph traversal

## 🔧 Development

### Local Development Setup

```bash
# Install dependencies
uv sync

# Set up pre-commit hooks
pre-commit install

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

### Code Quality

```bash
# Format code
uv run black .
uv run isort .

# Lint code
uv run flake8 .
```

### Testing

```bash
# Run tests
uv run python manage.py test

# Run with coverage
uv run coverage run --source='.' manage.py test
uv run coverage report
```

## 📁 Project Structure

```
awesome-jermocik-chatbot/
├── accounts/           # User authentication
├── chat/              # Chat functionality
├── core/              # Core utilities
├── etl/               # ETL pipeline
│   ├── extractors/    # VLM extractors
│   ├── processors/    # Pipeline logic
│   ├── input/         # PDF input directory
│   └── output/        # Processing results
├── rag/               # RAG engine
├── responder/         # Multi-agent responders
├── django_api_project/ # Django settings
└── docker files...
```

## 🔐 Security & Environment Variables

### Required Environment Variables

```env
# Django
SECRET_KEY=your-secret-key-here
DEBUG=False

# Database
DB_NAME=django_api_db
DB_USER=postgres  
DB_PASSWORD=secure-password

# OpenAI
OPENAI_API_KEY=sk-proj-...

# Neo4j
NEO4J_USER=neo4j
NEO4J_PASSWORD=secure-password
```

### Security Best Practices

- Change default passwords in production
- Use strong SECRET_KEY
- Set DEBUG=False in production
- Regularly update dependencies
- Monitor API usage and logs

## 🚨 Troubleshooting

### Common Issues

1. **Docker Memory Issues**: Increase Docker memory allocation to 8GB+
2. **OpenAI API Errors**: Verify API key and billing status
3. **Database Connection**: Ensure PostgreSQL health checks pass
4. **Neo4j Connection**: Check Neo4j service startup logs

### Debugging

```bash
# View logs
make logs

# Connect to web container
docker compose exec web bash

# Check database connection
make db-shell

# View specific service logs
docker compose logs web
docker compose logs db
docker compose logs neo4j
```

### Performance Optimization

- Monitor ETL pipeline processing time
- Adjust RAG similarity thresholds
- Consider GPU acceleration for VLM processing
- Optimize database indexes for vector queries

## 📈 Monitoring & Analytics

The system includes comprehensive logging:

- ETL pipeline progress and errors
- RAG retrieval performance
- Chat conversation analytics
- Database query optimization

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
