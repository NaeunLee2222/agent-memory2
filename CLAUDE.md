# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an Enhanced Agentic AI PoC (Proof of Concept) system that implements an intelligent agent platform with advanced memory management, MCP (Model Context Protocol) tool integration, and real-time feedback processing. The system demonstrates multi-agent learning capabilities with procedural, episodic, and working memory systems.

## Development Commands

### Starting the System
```bash
# Start all services with Docker Compose
docker-compose up --build

# Check backend connectivity status
./backend_connect_status.sh

# Test memory API endpoints
./memory_api_test.sh
```

### Service Access Points
- Frontend (Streamlit): http://localhost:8501
- Backend API: http://localhost:8100
- API Documentation: http://localhost:8100/docs
- Prometheus Monitoring: http://localhost:9090
- Grafana Dashboard: http://localhost:3001 (admin:admin)
- Neo4j Browser: http://localhost:7474 (neo4j:testpassword)

### Evaluation and Testing
```bash
# Run comprehensive PoC evaluation
cd evaluation
pip install requests pandas
python poc_evaluator.py

# Run individual performance tests
python memory_tests.py
python feedback_tests.py
python performance_monitor.py
```

### Container Management
```bash
# View backend logs
docker logs enhanced-agentic-ai-poc-backend-1

# View frontend logs  
docker logs enhanced-agentic-ai-poc-frontend-1

# Restart specific service
docker-compose restart backend
```

## Architecture Overview

### Core Components

**Backend (FastAPI)**
- `main.py`: Primary API server with chat endpoints and LLM-based tool planning
- `agent/`: Agent execution logic (executor.py, planner.py, reasoner.py)
- `memory/`: Multi-tier memory system (procedural, semantic, working memory)
- `mcp/`: Model Context Protocol integration (connector.py, tool_registry.py)
- `services/`: Business logic services for memory, feedback, and MCP operations

**Frontend (Streamlit)**
- Interactive web interface for agent interactions
- Real-time feedback collection and session management
- Performance monitoring dashboard integration

**MCP Tools System**
- `mcp_tools/`: Standalone MCP server with communication and utility tools
- Tools include: emergency_mail, generate_msg, search_db, send_slack
- Tool categories: communication_tools, data_tools, document_tools, utility_tools

### Memory Architecture

The system implements a three-tier memory architecture:

1. **Working Memory** (`memory/working_memory.py`): Short-term context and session management
2. **Procedural Memory** (`memory/procedural_memory.py`): Pattern learning and workflow automation  
3. **Semantic Memory** (`memory/semantic_memory.py`): Long-term knowledge storage and retrieval

Memory operations are backed by:
- Redis: Fast cache and session storage
- ChromaDB: Vector embeddings for semantic search
- Neo4j: Graph relationships for procedural patterns

### Key Features

**Agent Execution Flow**
1. User message received via `/chat` endpoint
2. LLM generates tool execution plan based on available MCP tools
3. Tools executed sequentially with enhanced parameters from context
4. Results stored in working memory for future reference
5. Feedback collected for continuous system improvement

**Cross-Agent Learning**
- Agents share learned patterns through semantic memory
- Procedural memory captures and replays successful workflows
- Feedback loop enables real-time system optimization

## Configuration

### Environment Variables
Required environment variables (set in `.env`):
```
OPENAI_API_KEY=your_openai_key
MEM0_API_KEY=your_mem0_key  
```

### Database Configuration
- Redis: Port 6380 (external), 6379 (internal)
- ChromaDB: Port 8001 (external), 8000 (internal)
- Neo4j: Ports 7474 (HTTP), 7687 (Bolt)

### Performance Targets
- Average response time: <3 seconds
- Memory retrieval: <200ms
- Feedback processing: <5 seconds (95% of requests)
- System availability: >99%
- Concurrent users: 100+

## Development Notes

### Agent Modes
- **Basic Mode**: Simple request-response without memory integration
- **Flow Mode**: Full memory-enabled mode with pattern learning and context retention

### MCP Tool Integration
The system dynamically discovers and integrates MCP tools. New tools should be added to `mcp_tools/tools/` with appropriate categorization.

### Memory System Usage
- Use `MemoryDatabase` for basic CRUD operations
- Leverage `WorkingMemory` for session context management
- Implement `ProceduralMemory` for workflow pattern recognition
- Access `SemanticMemory` for knowledge-based retrieval

### Monitoring and Observability
- Prometheus metrics available for request duration, memory operations, and system health
- Grafana dashboards provide real-time performance visualization
- Structured logging throughout the application for debugging

### Testing Strategy
- Unit tests for individual memory components
- Integration tests for agent workflows
- Performance benchmarks for response times and memory operations
- End-to-end evaluation scenarios for PoC validation