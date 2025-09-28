# Copyright 2025 Emad Noorizadeh
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# simple_rag.py
import os, json
from typing import List, Dict, Any, Optional, Tuple

import chromadb
from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.llms.openai import OpenAI as LlamaIndexOpenAI

try:
    from openai import OpenAI as OpenAIClient
except Exception:
    OpenAIClient = None

from ..utils.utils_json import coerce_json
from answer_schema import AnswerSchema

PROMPT_TEMPLATE = (
    "You are a financial assistant.\n"
    "Answer the user's question using ONLY the information in the Context.\n"
    "You may:\n"
    "  • paraphrase or rephrase facts\n"
    "  • combine facts across multiple context chunks\n"
    "  • do arithmetic, conversions, or simple reasoning grounded in context\n"
    "Do NOT invent information not present in the context.\n\n"
    "If the context is partially sufficient, return what is supported and note what is missing.\n"
    "If it is insufficient, return the following JSON object:\n"
    "{{{{ \"answer\": \"This question cannot be answered from the provided context.\", "
    "\"evidence\": [], \"missing\": \"All information missing.\", "
    "\"confidence\": \"Low\", \"faithfulness_score\": 0.0, \"completeness_score\": 0.0, "
    "\"answer_type\": \"abstain\", \"abstained\": true, \"reasoning_notes\": \"Insufficient context\" }}}}\n\n"
    "The JSON object must contain the following keys:\n"
    "- \"answer\": string → concise grounded answer\n"
    "- \"evidence\": [string] → list of chunk IDs or supporting snippets\n"
    "- \"missing\": string → what info is missing, or \"None\"\n"
    "- \"confidence\": string → one of High, Medium, or Low\n"
    "- \"faithfulness_score\": number → 0.0–1.0, groundedness of the answer\n"
    "- \"completeness_score\": number → 0.0–1.0, how fully the question was answered\n"
    "- \"answer_type\": string → fact | list | numeric | inference | abstain\n"
    "- \"abstained\": boolean → true if the model could not answer\n"
    "- \"reasoning_notes\": string → brief justification (1–2 sentences)\n\n"
    "Here is the JSON skeleton you must follow (no comments, no extra fields):\n"
    "{{{{\n"
    "  \"answer\": \"\",\n"
    "  \"evidence\": [],\n"
    "  \"missing\": \"\",\n"
    "  \"confidence\": \"\",\n"
    "  \"faithfulness_score\": 0.0,\n"
    "  \"completeness_score\": 0.0,\n"
    "  \"answer_type\": \"\",\n"
    "  \"abstained\": false,\n"
    "  \"reasoning_notes\": \"\"\n"
    "}}}}\n\n"
    "Cite evidence ONLY from these chunk IDs: [{{valid_chunk_ids}}]. "
    "Do not invent new IDs (e.g., Ck) or ranges. Using an ID not in the list is an error.\n\n"
    "⚠️ Return ONLY one JSON object on a single line.\n"
    "Use strict JSON: double quotes for all keys and string values, commas between fields, "
    "and colons exactly once per key.\n"
    "Do not include code fences, markdown, or any extra text before or after the JSON.\n\n"
    "### Context:\n{{context}}\n\n"
    "### Question:\n{{question}}\n\n"
    "### JSON Answer:"
)

# A short repair prompt used only on schema failure
REPAIR_PROMPT = (
    "Your previous output was not valid according to the required JSON schema.\n"
    "Fix it and return ONE LINE of strict JSON with the required keys (no code fences, no extra text).\n"
    "Original invalid output:\n{bad}\n\n"
    "Reprint the corrected JSON now:"
)

class SimpleRAG:
    def __init__(
        self,
        collection_name: str,
        db_path: str = "./chroma_db",
        system_role: str = "You are a financial assistant.",
        default_top_k: int = 3,
        li_model: str = "gpt-4o-mini",
        oi_model: str = "gpt-4o-mini",
        openai_base_url: Optional[str] = None,
        openai_api_key_env: str = "OPENAI_API_KEY",
        temperature: float = 0.0,
        max_retries: int = 1,   # retry count on schema/parse failure
    ):
        self.collection_name = collection_name
        self.db_path = db_path
        self.system_role = system_role
        self.default_top_k = default_top_k
        self.li_model = li_model
        self.oi_model = oi_model
        self.openai_base_url = openai_base_url
        self.openai_api_key_env = openai_api_key_env
        self.temperature = temperature
        self.max_retries = max_retries

        self._client = chromadb.PersistentClient(path=self.db_path)
        collection = self._client.get_or_create_collection(self.collection_name)
        self._chroma_store = ChromaVectorStore(chroma_collection=collection)
        self._index = VectorStoreIndex.from_vector_store(self._chroma_store)

        self.last_retrieved: List[Dict[str, Any]] = []
        self.last_context: str = ""
        self.last_valid_ids: List[str] = []

    # ---------- Retrieval ----------
    def retrieve(self, question: str, top_k: Optional[int] = None) -> List[Any]:
        k = top_k or self.default_top_k
        retriever = self._index.as_retriever(similarity_top_k=k)
        return retriever.retrieve(question)

    def _format_context_from_nodes(
        self, nodes: List[Any]
    ) -> Tuple[str, List[Dict[str, Any]], List[str], List[str]]:
        labeled, debug, valid_ids, texts = [], [], [], []
        for i, node in enumerate(nodes):
            raw = getattr(node, "node", node)
            text = raw.get_content() if hasattr(raw, "get_content") else getattr(raw, "text", "") or ""
            meta = getattr(raw, "metadata", {}) or {}
            source = meta.get("source") or meta.get("file_path") or meta.get("document_id") or "unknown"
            cid = f"C{i+1}"
            valid_ids.append(cid)
            labeled.append(f"{cid}: {text}")
            texts.append(text)
            debug.append({"rank": i + 1, "source": source, "chars": len(text)})
        return "\n\n".join(labeled), debug, valid_ids, texts

    def build_prompt(self, context: str, question: str, valid_chunk_ids: str) -> str:
        from collections import defaultdict
        return PROMPT_TEMPLATE.format_map(
            defaultdict(str, context=context, question=question, valid_chunk_ids=valid_chunk_ids)
        )

    # ---------- LLM calls ----------
    def _answer_via_llamaindex_llm(self, prompt: str) -> str:
        llm = LlamaIndexOpenAI(model=self.li_model, temperature=self.temperature)
        resp = llm.complete(prompt)
        return (resp.text or "").strip()

    def _answer_via_openai_chat(self, prompt: str, question: str) -> str:
        if OpenAIClient is None:
            raise RuntimeError("OpenAI SDK not installed. Run: pip install openai>=1.0.0")
        api_key = os.getenv(self.openai_api_key_env, "")
        if not api_key:
            raise RuntimeError(f"Missing API key. Set {self.openai_api_key_env} in your environment.")
        client_kwargs = {"api_key": api_key}
        if self.openai_base_url:
            client_kwargs["base_url"] = self.openai_base_url
        client = OpenAIClient(**client_kwargs)
        chat = client.chat.completions.create(
            model=self.oi_model,
            temperature=self.temperature,
            messages=[{"role": "system", "content": prompt}, {"role": "user", "content": question}],
        )
        return (chat.choices[0].message.content or "").strip()

    # ---------- Parsing + schema ----------
    def _normalize_output_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Validate/normalize with Pydantic
        model = AnswerSchema(**data)
        norm = model.dict()

        # Ensure strings for CSV safety where needed
        def _s(x):
            if isinstance(x, str):
                return x
            try:
                return json.dumps(x, ensure_ascii=False)
            except Exception:
                return str(x)

        norm["answer"] = _s(norm.get("answer", ""))
        norm["missing"] = _s(norm.get("missing", ""))
        norm["confidence"] = _s(norm.get("confidence", ""))
        norm["answer_type"] = _s(norm.get("answer_type", ""))
        norm["reasoning_notes"] = _s(norm.get("reasoning_notes", ""))
        return norm

    def _parse_then_validate(self, raw: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Returns (normalized_dict_or_None, error_msg_or_None)."""
        try:
            data = coerce_json(raw) or {}
            if not isinstance(data, dict):
                data = {"answer": str(data)}
            norm = self._normalize_output_dict(data)
            return norm, None
        except Exception as e:
            return None, f"{type(e).__name__}: {e}"

    def _repair_prompt(self, bad: str) -> str:
        return REPAIR_PROMPT.format(bad=bad)

    # ---------- Public one-call ----------
    def answer(
        self,
        question: str,
        top_k: Optional[int] = None,
        backend: str = "llamaindex",
        show_chunks: bool = False,
    ) -> Dict[str, Any]:
        nodes = self.retrieve(question, top_k=top_k)
        context, debug_meta, valid_ids, chunk_texts = self._format_context_from_nodes(nodes)

        self.last_retrieved = [{"rank": m["rank"], "source": m["source"], "text_len": m["chars"]} for m in debug_meta]
        self.last_context = context
        self.last_valid_ids = valid_ids

        if show_chunks:
            print("🔍 Retrieved Chunks:")
            for c in debug_meta:
                print(f"- #{c['rank']} | source: {c['source']} | {c['chars']} chars")

        prompt = self.build_prompt(context=context, question=question, valid_chunk_ids=", ".join(valid_ids))

        # First attempt
        raw1 = self._answer_via_llamaindex_llm(prompt) if backend == "llamaindex" else self._answer_via_openai_chat(prompt, question)
        norm, err = self._parse_then_validate(raw1)

        retries_left = self.max_retries
        raw_used = raw1
        while norm is None and retries_left > 0:
            # Re-prompt with the error + original bad output
            repair = self._repair_prompt(raw1 if len(raw1) < 6000 else raw1[:6000])
            raw2 = self._answer_via_llamaindex_llm(repair) if backend == "llamaindex" else self._answer_via_openai_chat(repair, question)
            norm, err = self._parse_then_validate(raw2)
            raw_used = raw2
            retries_left -= 1

        if norm is None:
            # Final mock fallback
            norm = AnswerSchema(
                answer="This question cannot be answered due to schema/parse failure.",
                evidence=[],
                context_utilization=[],
                missing="SchemaValidationFailed",
                confidence="Low",
                faithfulness_score=0.0,
                completeness_score=0.0,
                answer_type="abstain",
                abstained=True,
                reasoning_notes="Model failed to produce valid JSON after retries."
            ).dict()
            norm["raw"] = raw_used

        # attach extras
        norm.update({
            "prompt": prompt,
            "chunk_texts": chunk_texts,
            "context": context,
            "valid_chunk_ids": valid_ids,
        })
        return norm

    def set_system_role(self, role: str) -> None:
        self.system_role = role
