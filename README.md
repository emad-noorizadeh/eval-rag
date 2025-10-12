# RAG Testing Interface

A web interface for testing and evaluating Retrieval-Augmented Generation (RAG) systems using Next.js frontend and FastAPI backend with ChromaDB for vector storage.

**Author:** [username]

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
   source /path/to/your/venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up models path (choose one method):

   **Method A: Use default path**
   ```bash
   # Create default models directory
   mkdir -p /home/[username]/models
   
   # Download All-MiniLM model
   python setup/minilm_loader.py
   ```

   **Method B: Use custom path**
   ```bash
   # Set custom models path
   export MODELS_PATH="/path/to/your/models"
   
   # Create directory and download model
   mkdir -p "$MODELS_PATH"
   python setup/minilm_loader.py
   ```

5. Start the FastAPI server:
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

## Quick Start

### Complete Setup (Copy-Paste)

**Backend:**
```bash
cd backend
source /path/to/your/venv/bin/activate
pip install -r requirements.txt
mkdir -p /home/[username]/models
python setup/minilm_loader.py
python main.py
```

**Frontend:**
```bash
cd frontend
npm install
echo "NEXT_PUBLIC_BACKEND_URL=http://localhost:9000" > .env.local
echo "BACKEND_URL=http://localhost:9000" >> .env.local
npm run dev
```

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
- **Host**: 0.0.0.0 (all interfaces)

#### Models Path Configuration

The system uses a configurable models path system instead of storing models in the repository.

##### Default Models Path
- **Default Location**: `/home/[username]/models`
- **Environment Variable**: `MODELS_PATH` (optional)

##### Setting Up Models Path

**Method 1: Use Default Path (Recommended)**
```bash
# Create the default models directory
mkdir -p /home/[username]/models

# Download the All-MiniLM model
cd backend
python setup/minilm_loader.py
```

**Method 2: Custom Models Path**
```bash
# Set custom models directory
export MODELS_PATH="/path/to/your/models"

# Create the directory
mkdir -p "$MODELS_PATH"

# Download the All-MiniLM model
cd backend
python setup/minilm_loader.py
```

**Method 3: Environment Variable in .env**
```bash
# Add to backend/.env
echo "MODELS_PATH=/path/to/your/models" >> backend/.env
```

##### Models Path Examples

**Local Development:**
```bash
export MODELS_PATH="/home/[username]/models"
```

**Production Server:**
```bash
export MODELS_PATH="/opt/rag-system/models"
```

**Docker/Container:**
```bash
export MODELS_PATH="/app/models"
```

**Shared Network Storage:**
```bash
export MODELS_PATH="/mnt/shared/models"
```

##### Downloading All-MiniLM Model

The system will automatically download the All-MiniLM model if not found locally:

```bash
cd backend
python setup/minilm_loader.py
```

This will:
1. Download `sentence-transformers/all-MiniLM-L6-v2` from HuggingFace
2. Save it to your configured models path
3. Verify the model was saved correctly

##### Model Loading Behavior

- **Local Model Found**: Uses local model from `MODELS_PATH`
- **Local Model Missing**: Falls back to HuggingFace download
- **Download Failed**: Uses HuggingFace model directly (slower)

##### Verifying Models Setup

```bash
# Check models path configuration
cd backend
python -c "from utils.models_path import get_model_info; import json; print(json.dumps(get_model_info(), indent=2))"

# Test model loading
python -c "from utils.metric_utils import _maybe_load_embedder; model = _maybe_load_embedder(); print('Model loaded:', model is not None)"
```

##### Troubleshooting Models Path

**Problem**: Model not found locally
**Solution**: Run `python setup/minilm_loader.py` to download the model

**Problem**: Permission denied creating models directory
**Solution**: Ensure write permissions to the models path directory

**Problem**: Model loading fails
**Solution**: Check that the models directory contains the `all-MiniLM-L6-v2` folder

**Problem**: Slow model loading
**Solution**: Ensure the model is downloaded locally rather than using HuggingFace fallback

### Frontend Configuration

#### Backend URL Configuration

The frontend can be configured to connect to different backend URLs using environment variables.

##### Method 1: Environment Variables (Recommended)

Create or update `frontend/.env.local`:

```bash
# Backend API Configuration
NEXT_PUBLIC_BACKEND_URL=http://localhost:9000
BACKEND_URL=http://localhost:9000
```

##### Configuration Examples

**Local Development:**
```bash
NEXT_PUBLIC_BACKEND_URL=http://localhost:9000
BACKEND_URL=http://localhost:9000
```

**Production Server:**
```bash
NEXT_PUBLIC_BACKEND_URL=https://your-api-server.com
BACKEND_URL=https://your-api-server.com
```

**Custom Port:**
```bash
NEXT_PUBLIC_BACKEND_URL=http://localhost:8080
BACKEND_URL=http://localhost:8080
```

**Docker/Container:**
```bash
NEXT_PUBLIC_BACKEND_URL=http://backend:9000
BACKEND_URL=http://backend:9000
```

##### Environment Variables Explained

- **`NEXT_PUBLIC_BACKEND_URL`**: Used for client-side API calls (browser)
- **`BACKEND_URL`**: Used for server-side API routes (Next.js API routes)

##### Files That Support Environment Variables

✅ **Already configured:**
- `frontend/src/app/api/chat-config/route.ts`
- `frontend/src/app/api/chunking-config/route.ts`
- `frontend/src/app/api/documents/route.ts`
- `frontend/src/app/api/documents/[filename]/content/route.ts`
- `frontend/src/app/api/documents/[filename]/metadata/route.ts`
- `frontend/src/services/sessionService.ts`
- `frontend/src/config/api.ts`

##### Quick Setup

1. **Create environment file:**
   ```bash
   cd frontend
   echo "NEXT_PUBLIC_BACKEND_URL=http://localhost:9000" > .env.local
   echo "BACKEND_URL=http://localhost:9000" >> .env.local
   ```

2. **Restart development server:**
   ```bash
   npm run dev
   ```

##### Testing Configuration

1. **Check environment variables:**
   ```bash
   cd frontend
   echo $NEXT_PUBLIC_BACKEND_URL
   ```

2. **Test backend connection:**
   ```bash
   curl http://your-backend-url:9000/health
   ```

3. **Check browser console** for any connection errors

##### Troubleshooting Backend URL Issues

- **CORS Errors**: Ensure backend allows requests from your frontend domain
- **Connection Refused**: Verify backend is running and accessible
- **Environment Variables**: Always restart the development server after changing `.env.local`
- **HTTPS**: Use HTTPS in production for security

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
4. **Backend Connection Issues**: Check that `NEXT_PUBLIC_BACKEND_URL` and `BACKEND_URL` are correctly set
5. **Environment Variables**: Restart the development server after changing `.env.local`

### Backend URL Issues

**Problem**: Frontend can't connect to backend
**Solutions**:
- Verify backend is running: `curl http://localhost:9000/health`
- Check environment variables in `frontend/.env.local`
- Ensure both `NEXT_PUBLIC_BACKEND_URL` and `BACKEND_URL` are set
- Restart frontend development server after changing environment variables

**Problem**: CORS errors in browser console
**Solutions**:
- Verify backend CORS settings in `backend/config/config.py`
- Check that frontend URL is in allowed origins
- Ensure backend is running on the correct host/port

**Problem**: API routes return 500 errors
**Solutions**:
- Check `BACKEND_URL` environment variable for server-side API routes
- Verify backend is accessible from the server-side context
- Check backend logs for detailed error messages

### Logs

- Backend logs are displayed in the terminal where you run `python main.py`
- Frontend logs are available in the browser console and terminal
- API route logs are available in the Next.js development server terminal

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

Copyright 2025 [username]
