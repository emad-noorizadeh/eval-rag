# RAG Testing Interface

Modern evaluation harness for Retrieval-Augmented Generation (RAG) systems. The repo ships with a Next.js frontend, FastAPI backend, persistent ChromaDB store, and a streamlined LangGraph router that combines retrieval gating with the guarded answer LLM to handle clarifications, routing, and abstention.

---

## High-Level Capabilities

- **Document ingestion & semantic retrieval** – Index local text with OpenAI embeddings stored in Chroma, including automatic metadata extraction.
- **Router-guided conversations** – A lightweight LangGraph state machine gates retrieval and lets the guarded answer LLM drive answer/clarify/abstain outcomes while keeping clarification state per session.
- **Startup health checks** – Database initialization now validates embedding dimensionality and resets mismatched collections safely.
- **API key resilience** – OpenAI credentials resolve from environment variables, config, or a local fallback file (`~/.openai_key`), so automation runs in clean shells.
- **Schema repair** – Guarded answer responses are schema-validated; invalid JSON triggers an automatic repair prompt up to `models.llm_max_retry` times (default 1).
- **Observability** – Consistent logging of router decisions, clarification counts, coverage metrics, and storage stats.

---

## Repository Layout

```
frontend/                # Next.js application
backend/                 # FastAPI backend + router/agent
├── main.py              # API entry point
├── config/              # Config loader + Chroma safeguards
├── router_graph.py      # Intelligent router
├── rag.py               # RAG answer generation pipeline
├── utils/               # Helpers (conversation utils, metadata, etc.)
└── scripts/             # CLI utilities (create/delete index, etc.)
data/                    # Source documents (ignored except for .gitkeep)
chroma_db/               # Persistent Chroma storage
index/                   # Derived document metadata JSON
logs/                    # Backend log outputs
README.md
```

---

## Backend Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
```

### OpenAI Credentials

The backend resolves `OPENAI_API_KEY` in this order:
1. Explicit argument when constructing `ModelManager`.
2. Environment variable `OPENAI_API_KEY`.
3. `config.json` value `models.api_key` (if populated).
4. Fallback file `~/.openai_key` (plain text key, no quotes).

This makes CLI scripts (e.g. `create_index`) robust even in clean shells. If none are found, `ModelManager` raises a clear error.

**LLM retry:** The guarded answer call will attempt up to `models.llm_max_retry` schema repairs (default `1`). Override this in `config.json` or via `RAG_LLM_MAX_RETRY` if you need more retries.

**Deterministic generation:** The default `models.temperature` is `0.0` to keep responses stable. Raise it if you want more creative variability.

### Starting the API

```bash
source venv/bin/activate
OPENAI_API_KEY=... ./venv/bin/python -m backend.main
# or rely on config.json / ~/.openai_key fallback
```

The server boots on `http://localhost:9000`, prints configuration details, and runs the embedding shape audit described below.

---

## Frontend Setup

```bash
cd frontend
npm install
echo "NEXT_PUBLIC_BACKEND_URL=http://localhost:9000" > .env.local
npm run dev
```

The Next.js UI listens on `http://localhost:4000`.

---

## Embedding Index Lifecycle

### Building / Rebuilding the Index

```bash
./venv/bin/python -m backend.scripts.create_index \
  --overwrite \
  --source-folder backend/data
```

- `--overwrite` clears the existing Chroma collection via the safeguarded delete routine.
- `source-folder` defaults to `backend/data`; point it anywhere with structured text.
- The script will back up mismatched collections, rebuild with OpenAI embeddings (1536-dim), and store metadata snapshots in `index/metadata`.

### Startup Embedding Audit

`backend/config/database_config.py` now:
- Verifies stored embedding dimensions using `collection.peek() / get(limit=5)`.
- Resets and backs up collections if vectors have the wrong size (e.g., legacy mock embeddings).
- Prints dimension mismatches and directs you to rebuild.

This guarantees alignment between configured embedding model and stored vectors.

---

## LangGraph Router Architecture

The intelligent path is implemented in `backend/router_graph.py` as a LangGraph `StateGraph`. Every user turn walks the same deterministic graph, allowing you to reason about routing decisions node-by-node while still keeping the guarded answer LLM as the single “truth oracle”.

### State Model

`AgentState` is a typed dictionary that LangGraph threads through the graph. It has three buckets of fields:

- **Persistent session metadata** – `last_question`, `awaiting_clarification`, `clarify_count`, `last_clarification`, `topic_hint`, and `session_id`. These survive across turns and are stored on the FastAPI session object.
- **Conversation history** – `messages` is declared as an accumulating list (`Annotated[..., operator.add]`), so each node can append without reimplementing merging logic.
- **Turn-local scratchpad** – All intermediate values (`user_message`, `effective_question`, `retrieved_chunks`, `avg_similarity`, `rag_response`, `decision`, etc.) live here and are replaced every turn.

This separation keeps the graph pure (all state is explicit) and makes it easy to snapshot the router at any point for debugging.

### Node Breakdown

| Node | Purpose | Key logic |
| --- | --- | --- |
| `ingest` | Normalize the incoming message | Appends the raw user message to `messages` and ensures the persistent metadata keys are initialized. |
| `frustration` | Short-circuit on obvious frustration | Looks for frustration tokens (e.g., “confusing”, “hard”) in non-question utterances. When triggered it returns a stock clarification question without touching retrieval or the LLM, increments `clarify_count`, and marks the decision as `clarification`. |
| `build_query` | Derive the “effective” question for retrieval | Handles acknowledgements and follow-ups: if the user is replying to an earlier clarification or sends a short fragment, it stitches the fragment to the previous interpreted question; acknowledgements reuse the last question entirely. The result is stored as `effective_question`, and we note whether history was appended (used later for metrics/UI). |
| `retrieve` | Fetch candidate context | Calls `RAG.retrieve_documents` once using the configured `top_k`. Scores and average similarity are cached in the state so downstream nodes and metrics do not redo the work. |
| `answer` | Run the guarded answer LLM | Builds a conversation snippet (last *k* turns) plus the current `topic_hint`, then calls `RAG.generate_response`. The raw RAG payload (answer, metrics, sources) is saved in `rag_response`. |
| `decide` | Interpret the LLM response | Reads `rag_response.metrics`. If the model abstained and supplied a `clarifying_question`, we switch to clarification mode and increment `clarify_count`. A bare abstain becomes an `abstain` decision. Otherwise we treat it as an answer. The resolved `answer_text`, `decision`, `clarification_question`, and latest `interpreted_question` are written to the state. |
| `finalize` | Assemble the public response and persist session state | Builds the rich metrics blob via `ChatAgent._create_intelligent_metrics`, converts raw chunks into `sources`, attaches retrieval metadata, and stamps timestamps. It also updates persistent metadata so the next turn knows whether we are awaiting a clarification and what the “topic hint” should be. Any retrieval errors from the RAG pipeline are surfaced here with a graceful message. Finally the compiled response is placed in `state["response"]` and the assistant turn is appended to the conversation history. |

The graph wiring is linear except for the optional fast-path out of `frustration`:

```
START → ingest → frustration ──┐
                               ├─ skip_to_finalize → finalize → END
                               └─ continue → build_query → retrieve → answer → decide → finalize → END
```

### Session Integration & Metrics

- **ChatAgent integration** – `SimpleRouterApp.invoke` receives the current FastAPI session state (if any), executes the graph, then writes back the updated metadata (`messages`, `last_question`, `awaiting_clarification`, etc.). That is how the router “remembers” clarifications across HTTP requests.
- **Single LLM call** – Even though the graph has multiple nodes, the guarded answer model is invoked exactly once per turn (inside `answer`). All branching is performed deterministically using the model’s structured JSON response.
- **Debug output** – `finalize` calls `ChatAgent._create_intelligent_metrics`, which merges the base metrics from the LLM with retrieval stats (scores, context length, chunk IDs), ingest summaries, and clarification bookkeeping. These metrics feed the frontend debug panel, including the new context-utilization highlights.

Together, these pieces give you a transparent router: you can inspect the state entering or leaving any node, replay hops during debugging, and extend the graph (for example, by inserting a tool-use branch) without altering the core ChatAgent API.

---

## MiniLM Model Storage

Sentence-transformer retrieval depends on a local copy of `sentence-transformers/all-MiniLM-L6-v2`. The loader (`backend/setup/minilm_loader.py`) saves the model under a configurable `MODELS_PATH` so the backend can run fully offline.

1. **Choose a model directory**
   - Default: `/Users/[username]/Projects/models`
   - Override by exporting `MODELS_PATH=/absolute/path/to/models` (use `~` for home if you prefer; the loader expands it).  
   - Whichever value you pick is persisted and used everywhere that calls `backend.utils.models_path`.

2. **Download/initialize the model**
   ```bash
   source venv/bin/activate
   python -m backend.setup.minilm_loader
   ```
   The script pulls `all-MiniLM-L6-v2`, ensures the models directory exists, and writes it to `<MODELS_PATH>/all-MiniLM-L6-v2/`.

3. **Verify configuration**
   ```bash
   python -m backend.utils.models_path
   ```
   This prints the resolved models path, whether the directory exists, and if the MiniLM folder is present. The backend will automatically load MiniLM from that location when retrieval starts.

Run the loader again any time you relocate models or want to refresh the cache.

---

## Interactive Configurator

For quick setup without hand-editing `config.json`, use the interactive helper:

```bash
source venv/bin/activate
python -m backend.setup.configurator
```

You will be prompted (optionally) to update:

- **Custom OpenAI base URL** – toggles `models.use_openai_url` and sets `models.base_url` (and mirrors the choice to `.env` via `OPENAI_BASE_URL`).
- **OpenAI API key** – stores the key in `config.json` and writes `OPENAI_API_KEY` into `.env` for local runs.
- **MODELS_PATH** – updates `.env` so the MiniLM loader and retrieval stack use your preferred local models directory.
- **Model defaults** – embedding/LLM model IDs, temperature, and max tokens all get written back to `config.json`.
- **Session auto-extend** – toggle whether the UI should auto-renew sessions on user activity (`session.auto_extend`).

Press Enter to keep existing values; the script only overwrites settings you supply. After running it, restart the backend to pick up the new configuration.

---

## Current Limitations & Next Steps

- Router decisions still depend on hand-coded keyword maps for intent/subject detection. Scaling to new domains will require retraining or more adaptive classifiers.
- Clarification prompts rely on heuristics and a single LLM format; they would benefit from data-driven evaluation and templating.
- No automated regression suite exists for router decisions (answer vs. clarify vs. abstain). Capturing interaction logs and training a classifier (distilled from LLM judgments) is the recommended evolution path.

See the “Router Evolution” section in the main README response for detailed design guidance.

---

## Useful Scripts

| Command | Purpose |
| --- | --- |
| `./venv/bin/python -m backend.scripts.create_index --overwrite --source-folder <dir>` | Rebuild Chroma index from a folder |
| `./venv/bin/python -m backend.scripts.delete_index --yes` | Clear the collection + metadata |
| `./venv/bin/python -m backend.tests.run_tests` | Run backend test suite (if enabled) |

---

## Logs & Troubleshooting

- **Backend console**: Shows API key resolution, database checks, router decisions, and embedding requests.
- **Logs directory**: `backend/logs/rag_system_local.log` collects structured events; `backend/logs/url_guardrail.log` captures network guardrail entries.
- **Common pitfalls**:
  - `Collection expecting embedding with dimension of 1`: rebuild index with a valid API key.
  - `type object 'ModelManager' has no attribute 'openai_client'`: ensure key resolution succeeded.
  - `TypeError: Failed to fetch` on UI load: restart backend (`./venv/bin/python -m backend.main`).

---

## Contributing

- Update `.gitignore` with local secrets (e.g., `backend/.env`) to avoid committing credentials.
- Run lint/tests before submitting PRs.
- Capture router decision logs when adding new heuristics; this facilitates regression checks.

---

## License

Apache 2.0 – see `LICENSE` for details.
