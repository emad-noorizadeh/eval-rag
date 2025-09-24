# Setup Scripts

This folder contains one-time setup and utility scripts for the RAG Frontend project.

## Scripts

### `setup_environment.py`
Complete environment setup script that creates a virtual environment and installs all dependencies.

**Usage:**
```bash
cd setup
python setup_environment.py
```

**What it does:**
- Checks Python version compatibility (3.8+)
- Creates a virtual environment in the project root (`../venv/`)
- Installs all requirements from `../requirements.txt`
- Installs spaCy model from `../wheels/` directory
- Creates convenient activation scripts (`activate_env.sh` and `activate_env.bat`)
- Provides clear next steps for running the application

**Prerequisites:**
- Python 3.8 or higher
- The `../requirements.txt` file must exist
- The `../wheels/` directory should contain spaCy model wheel

### `minilm_loader.py`
Downloads and saves the sentence-transformers model locally for offline use.

**Usage:**
```bash
cd setup
python minilm_loader.py
```

**What it does:**
- Downloads `sentence-transformers/all-MiniLM-L6-v2` from HuggingFace
- Saves the model to `../models/all-MiniLM-L6-v2/` (requires existing models directory)
- Enables offline model loading

**Prerequisites:**
- The `../models/` directory must already exist in the backend folder

**After running:**
```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('../models/all-MiniLM-L6-v2')
```

## Quick Start

1. **Set up the environment:**
   ```bash
   cd backend/setup
   python setup_environment.py
   ```

2. **Activate the environment:**
   ```bash
   # On Unix/Mac
   source activate_env.sh
   
   # On Windows
   activate_env.bat
   ```

3. **Start the application:**
   ```bash
   # Backend (Terminal 1)
   cd backend
   python main.py
   
   # Frontend (Terminal 2)
   cd frontend
   npm run dev
   ```

## Purpose

These scripts are meant to be run once during initial setup or when you need to:
- Download models
- Initialize databases
- Set up development environments
- Perform one-time configurations

They should not be part of the main application runtime.
