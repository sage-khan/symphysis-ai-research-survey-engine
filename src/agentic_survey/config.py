"""Config loading and validation.

Every prompt, hyperparameter, and variable value that shapes an agent's
behaviour lives in a YAML file under a survey's project folder, never in
Python source. This module only defines the schema and loads/validates it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class ConfigError(Exception):
    """Raised when a survey or agent config fails validation."""


@dataclass
class ModelConfig:
    provider: str  # "ollama" | "openai" | "anthropic" | "openrouter"
    name: str
    temperature: float = 0.7
    max_tokens: int = 1024
    top_p: float = 1.0
    seed: Optional[int] = None
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RagConfig:
    enabled: bool = False
    corpus_path: Optional[str] = None
    top_k: int = 5
    embedding_model: Optional[str] = None
    chunk_size: int = 800
    chunk_overlap: int = 100


@dataclass
class SamplingConfig:
    repeats: int = 3
    max_retries_on_malformed: int = 2
    agreement_threshold: float = 0.0  # 0 disables agreement gating


@dataclass
class AgentConfig:
    id: str
    role: str
    role_description: str
    system_prompt_template: str
    model: ModelConfig
    rag: RagConfig
    sampling: SamplingConfig
    instrument: str
    source_path: Path


@dataclass
class SurveyConfig:
    id: str
    title: str
    instrument: str
    instrument_params: Dict[str, Any]
    weighting: Dict[str, Any]
    root: Path
    agent_configs: List[Path]


def _read_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ConfigError(f"Config file did not parse to a mapping: {path}")
    return data


def load_agent_config(path: Path) -> AgentConfig:
    data = _read_yaml(path)
    for required in ("id", "role", "role_description", "system_prompt_template", "model", "instrument"):
        if required not in data:
            raise ConfigError(f"Agent config {path} missing required field '{required}'")

    model_data = data["model"]
    model = ModelConfig(
        provider=model_data["provider"],
        name=model_data["name"],
        temperature=float(model_data.get("temperature", 0.7)),
        max_tokens=int(model_data.get("max_tokens", 1024)),
        top_p=float(model_data.get("top_p", 1.0)),
        seed=model_data.get("seed"),
        extra=model_data.get("extra", {}) or {},
    )

    rag_data = data.get("rag", {}) or {}
    rag = RagConfig(
        enabled=bool(rag_data.get("enabled", False)),
        corpus_path=rag_data.get("corpus_path"),
        top_k=int(rag_data.get("top_k", 5)),
        embedding_model=rag_data.get("embedding_model"),
        chunk_size=int(rag_data.get("chunk_size", 800)),
        chunk_overlap=int(rag_data.get("chunk_overlap", 100)),
    )
    if rag.enabled and not rag.corpus_path:
        raise ConfigError(f"Agent config {path} enables RAG but sets no corpus_path")

    sampling_data = data.get("sampling", {}) or {}
    sampling = SamplingConfig(
        repeats=int(sampling_data.get("repeats", 3)),
        max_retries_on_malformed=int(sampling_data.get("max_retries_on_malformed", 2)),
        agreement_threshold=float(sampling_data.get("agreement_threshold", 0.0)),
    )

    return AgentConfig(
        id=data["id"],
        role=data["role"],
        role_description=data["role_description"],
        system_prompt_template=data["system_prompt_template"],
        model=model,
        rag=rag,
        sampling=sampling,
        instrument=data["instrument"],
        source_path=path,
    )


def load_survey_config(survey_dir: Path) -> SurveyConfig:
    survey_yaml = survey_dir / "survey.yaml"
    data = _read_yaml(survey_yaml)
    for required in ("id", "title", "instrument"):
        if required not in data:
            raise ConfigError(f"Survey config {survey_yaml} missing required field '{required}'")

    agents_dir = survey_dir / "agents"
    agent_configs = sorted(agents_dir.glob("*.yaml")) if agents_dir.exists() else []
    if not agent_configs:
        raise ConfigError(f"No agent configs found under {agents_dir}")

    return SurveyConfig(
        id=data["id"],
        title=data["title"],
        instrument=data["instrument"],
        instrument_params=data.get("instrument_params", {}) or {},
        weighting=data.get("weighting", {}) or {},
        root=survey_dir,
        agent_configs=agent_configs,
    )
