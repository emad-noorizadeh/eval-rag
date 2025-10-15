"""Backend package initialization for eval-rag."""

import warnings

try:  # pragma: no cover - defensive import to silence third-party warnings
    from pydantic._internal._generate_schema import UnsupportedFieldAttributeWarning
except (ImportError, ModuleNotFoundError):  # pragma: no cover
    UnsupportedFieldAttributeWarning = None

if UnsupportedFieldAttributeWarning is not None:
    warnings.filterwarnings("ignore", category=UnsupportedFieldAttributeWarning)
