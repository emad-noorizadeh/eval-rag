# RAG Frontend Backend

A configurable RAG (Retrieval-Augmented Generation) system with hybrid retrieval capabilities.

## 🏗️ Architecture

- **ChatAgent**: Configurable chat agent with intelligent routing
- **RetrievalService**: Unified retrieval service (semantic + hybrid)
- **RAG**: Pure generation with configurable retrieval
- **SessionManager**: Session management and cleanup
- **IndexBuilder**: Document processing and indexing

## 🚀 Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure the system**:
   ```bash
   cp config.sample.json config.json
   # Edit config.json with your settings
   ```

3. **Start the server**:
   ```bash
   python main.py
   ```

## 📚 Documentation

- **[Configuration](docs/configuration/)** - System configuration and settings
- **[Features](docs/features/)** - Advanced features and capabilities
- **[Architecture](docs/architecture/)** - System design and architecture
- **[Guides](docs/guides/)** - Implementation guides and tutorials
- **[API](docs/api/)** - API documentation and examples

## 🔧 Configuration

The system is highly configurable through `config.json`:

- **Retrieval Methods**: `semantic` or `hybrid`
- **Routing Strategies**: `intelligent` or `simple`
- **Metadata Extraction**: Configurable extraction methods
- **Session Management**: Timeout and cleanup settings

## 🎯 Key Features

- **Hybrid Retrieval**: Combines semantic, BM25, metadata, and heuristic search
- **Intelligent Routing**: Context-aware conversation management
- **Session Management**: 30-minute sessions with automatic cleanup
- **Metadata Extraction**: Advanced document processing
- **Configurable**: Easy to customize and extend

## 📡 API Endpoints

- `POST /chat` - Main chat endpoint
- `GET /chat-config` - Get current configuration
- `POST /chat-config` - Update configuration
- `POST /build-index` - Build document index
- `GET /documents` - List documents
- `POST /documents/file` - Upload documents

## 🧪 Testing

Run tests in the `tests/` directory:

```bash
python -m pytest tests/
```

## 📝 License

This project is licensed under the Apache 2.0 License - see the [LICENSE](../LICENSE) file for details.

Copyright 2025 Emad Noorizadeh
