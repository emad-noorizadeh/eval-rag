# RAG Testing Interface

A web interface for testing and evaluating Retrieval-Augmented Generation (RAG) systems using Next.js frontend and FastAPI backend with ChromaDB for vector storage.

**Author:** Emad Noorizadeh

## Features

- **Document Upload**: Add documents to the vector database with optional metadata
- **Semantic Search**: Query documents using natural language with similarity scoring
- **Document Management**: View, delete, and manage all stored documents
- **Real-time Interface**: Modern, responsive UI built with Next.js and Tailwind CSS
- **Local Storage**: All data stored locally using ChromaDB

## Tech Stack

### Frontend
- Next.js 14 with TypeScript
- Tailwind CSS for styling
- React hooks for state management

### Backend
- FastAPI with Python
- ChromaDB for vector storage
- Sentence Transformers for embeddings
- Uvicorn ASGI server

## Project Structure

```
rag-frontend/
├── frontend/                 # Next.js frontend application
│   ├── src/
│   │   ├── app/             # Next.js app directory
│   │   └── components/      # React components
│   └── package.json
├── backend/                 # FastAPI backend application
│   ├── main.py             # FastAPI application
│   ├── requirements.txt    # Python dependencies
│   └── chroma_db/          # ChromaDB data directory (created automatically)
└── README.md
```

## Setup Instructions

### Prerequisites

- Node.js 18+ and npm
- Python 3.9+
- Virtual environment (recommended)

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Activate your virtual environment:
   ```bash
   source /Users/emadn/Projects/pipven/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Start the FastAPI server:
   ```bash
   python main.py
   ```

   The API will be available at `http://localhost:9000`

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

   The application will be available at `http://localhost:4000`

## Usage

### 1. Upload Documents

- Navigate to the "Upload Documents" tab
- Enter document text in the text area
- Optionally add metadata in JSON format
- Click "Upload Document" to add it to the vector database

### 2. Query Documents

- Navigate to the "Query Documents" tab
- Enter your search query
- Adjust the number of results (1-20)
- Click "Search Documents" to find similar content
- View results with similarity scores and metadata

### 3. Manage Documents

- Navigate to the "View Documents" tab
- See all uploaded documents
- Delete individual documents or clear all
- Refresh to see the latest changes

## API Endpoints

### Documents
- `POST /documents` - Add a new document
- `GET /documents` - Get all documents
- `DELETE /documents/{id}` - Delete a specific document
- `DELETE /documents` - Clear all documents

### Query
- `POST /query` - Search for similar documents

## Configuration

### Backend Configuration

The backend uses the following default settings:
- **Embedding Model**: `all-MiniLM-L6-v2` (384 dimensions)
- **Similarity Metric**: Cosine similarity
- **Database**: ChromaDB with persistent storage
- **Port**: 9000

### Frontend Configuration

The frontend is configured to connect to the backend at `http://localhost:9000`. To change this, update the API URLs in the component files.

## Development

### Adding New Features

1. **Backend**: Add new endpoints in `main.py`
2. **Frontend**: Create new components in `src/components/`
3. **Styling**: Use Tailwind CSS classes for consistent styling

### Database

ChromaDB will automatically create a `chroma_db` directory in the backend folder to store the vector database. This directory contains all the embeddings and metadata.

## Troubleshooting

### Common Issues

1. **CORS Errors**: Ensure the backend is running on port 9000 and the frontend on port 4000
2. **Model Download**: The first run may take longer as it downloads the sentence transformer model
3. **Port Conflicts**: Make sure ports 4000 and 9000 are available

### Logs

- Backend logs are displayed in the terminal where you run `python main.py`
- Frontend logs are available in the browser console and terminal

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

Copyright 2025 Emad Noorizadeh
