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

"""
Interactive setup helper for configuring OpenAI endpoints and local model paths.

This script lets you override a handful of common configuration values without
editing `config.json` or `.env` manually. Each prompt is optional — press Enter
to keep the current setting and move on.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from backend.config import config as system_config
from backend.config import get_config, set_config

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"


def prompt(text: str, default: Optional[str] = None) -> str:
    """Prompt the user and return the entered value or default."""
    suffix = f" [{default}]" if default not in (None, "") else ""
    value = input(f"{text}{suffix}: ").strip()
    if not value:
        return default if default is not None else ""
    return value


def prompt_bool(text: str, default: bool) -> bool:
    """Prompt for a yes/no answer."""
    default_prompt = "Y/n" if default else "y/N"
    while True:
        value = input(f"{text} ({default_prompt}): ").strip().lower()
        if value == "" and default is not None:
            return default
        if value in {"y", "yes"}:
            return True
        if value in {"n", "no"}:
            return False
        print("Please enter 'y' or 'n'.")


def update_env_var(name: str, value: Optional[str]) -> None:
    """
    Update (or remove) an entry in the project .env file.

    The helper keeps unrelated lines intact, making this safe to run repeatedly.
    """
    if value is None:
        return

    lines = []
    if ENV_PATH.exists():
        lines = ENV_PATH.read_text(encoding="utf-8").splitlines()

    updated = False
    new_line = f"{name}={value}"

    for idx, line in enumerate(lines):
        if not line or line.strip().startswith("#"):
            continue
        key = line.split("=", 1)[0].strip()
        if key == name:
            lines[idx] = new_line
            updated = True
            break

    if not updated:
        lines.append(new_line)

    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"✓ Updated {ENV_PATH.relative_to(PROJECT_ROOT)} with {name}")


def configure_openai() -> None:
    """Collect OpenAI-specific overrides."""
    current_use_url = bool(get_config("models", "use_openai_url") or False)
    current_base_url = get_config("models", "base_url") or "https://api.openai.com/v1"

    use_url = prompt_bool("Use a custom OpenAI base URL?", current_use_url)
    set_config("models", "use_openai_url", use_url)

    if use_url:
        base_url = prompt(
            "Enter the OpenAI base URL",
            current_base_url if current_use_url else current_base_url,
        )
        if base_url:
            set_config("models", "base_url", base_url)

    api_key_default = get_config("models", "api_key") or os.getenv("OPENAI_API_KEY", "")
    api_key = prompt("Enter the OpenAI API key (stored in config.json)", api_key_default)
    if api_key:
        set_config("models", "api_key", api_key)
        # Keep .env in sync so local development picks it up
        update_env_var("OPENAI_API_KEY", api_key)


def configure_models_path() -> None:
    """Collect the local models directory settings."""
    default_path = os.getenv("MODELS_PATH") or "/Users/[username]/Projects/models"
    models_path = prompt("Enter MODELS_PATH for local SentenceTransformer models", default_path)
    if models_path:
        expanded = os.path.abspath(os.path.expanduser(models_path))
        update_env_var("MODELS_PATH", expanded)
        print(f"✓ MODELS_PATH set to {expanded}")


def configure_model_defaults() -> None:
    """Let the user override a few core model options."""
    embedding_model = prompt(
        "Embedding model ID",
        get_config("models", "embedding_model"),
    )
    if embedding_model:
        set_config("models", "embedding_model", embedding_model)

    llm_model = prompt(
        "Chat LLM model ID",
        get_config("models", "llm_model"),
    )
    if llm_model:
        set_config("models", "llm_model", llm_model)

    temperature_default = str(get_config("models", "temperature"))
    temperature_input = prompt(
        "LLM temperature",
        temperature_default,
    )
    if temperature_input:
        try:
            temperature = float(temperature_input)
            set_config("models", "temperature", temperature)
        except ValueError:
            print("⚠️  Temperature must be numeric. Keeping existing value.")

    max_tokens_default = str(get_config("models", "max_tokens"))
    max_tokens_input = prompt(
        "Max tokens per completion",
        max_tokens_default,
    )
    if max_tokens_input:
        try:
            max_tokens = int(max_tokens_input)
            set_config("models", "max_tokens", max_tokens)
        except ValueError:
            print("⚠️  Max tokens must be an integer. Keeping existing value.")


def main() -> None:
    print("=" * 60)
    print("RAG Environment Setup")
    print("=" * 60)
    print("Press Enter to keep an existing value. Nothing here is required.")
    print()

    configure_openai()
    configure_models_path()
    configure_model_defaults()

    system_config.save_config()
    print("\n✓ Configuration saved. Restart the backend to apply changes.")


if __name__ == "__main__":
    main()
