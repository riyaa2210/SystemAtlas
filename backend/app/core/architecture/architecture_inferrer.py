"""
Architecture inference engine.
Analyzes scan results to produce a high-level system architecture diagram:
layers, detected technologies, and directed relationships between layers.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from typing import Optional

from app.core.analyzer.analysis_result import FileAnalysisResult
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ── Technology detection signals ─────────────────────────────────────────────

# Maps (pattern_in_imports_or_path) → (layer, technology_label)
TECH_SIGNALS: list[tuple[str, str, str]] = [
    # Frontend frameworks
    ("react", "frontend", "React"),
    ("next", "frontend", "Next.js"),
    ("vue", "frontend", "Vue.js"),
    ("angular", "frontend", "Angular"),
    ("svelte", "frontend", "Svelte"),
    # Backend frameworks
    ("fastapi", "api_gateway", "FastAPI"),
    ("django", "api_gateway", "Django"),
    ("flask", "api_gateway", "Flask"),
    ("express", "api_gateway", "Express"),
    ("nestjs", "api_gateway", "NestJS"),
    ("spring", "api_gateway", "Spring Boot"),
    ("rails", "api_gateway", "Rails"),
    ("laravel", "api_gateway", "Laravel"),
    ("gin", "api_gateway", "Gin"),
    ("actix", "api_gateway", "Actix"),
    ("axum", "api_gateway", "Axum"),
    # Auth
    ("jwt", "auth", "JWT"),
    ("oauth", "auth", "OAuth"),
    ("passport", "auth", "Passport.js"),
    ("authlib", "auth", "Authlib"),
    ("bcrypt", "auth", "bcrypt"),
    ("argon2", "auth", "Argon2"),
    # Databases
    ("postgres", "database", "PostgreSQL"),
    ("postgresql", "database", "PostgreSQL"),
    ("mysql", "database", "MySQL"),
    ("sqlite", "database", "SQLite"),
    ("mongodb", "database", "MongoDB"),
    ("neo4j", "database", "Neo4j"),
    ("redis", "cache", "Redis"),
    ("memcached", "cache", "Memcached"),
    # ORMs / ODMs
    ("sqlalchemy", "database", "SQLAlchemy"),
    ("mongoose", "database", "Mongoose"),
    ("prisma", "database", "Prisma"),
    ("typeorm", "database", "TypeORM"),
    ("sequelize", "database", "Sequelize"),
    ("hibernate", "database", "Hibernate"),
    # Messaging
    ("kafka", "message_queue", "Kafka"),
    ("rabbitmq", "message_queue", "RabbitMQ"),
    ("celery", "message_queue", "Celery"),
    ("bull", "message_queue", "Bull"),
    ("sqs", "message_queue", "AWS SQS"),
    # Storage
    ("s3", "storage", "AWS S3"),
    ("gcs", "storage", "GCS"),
    ("azure_blob", "storage", "Azure Blob"),
    ("minio", "storage", "MinIO"),
    # AI / ML
    ("openai", "ai_services", "OpenAI"),
    ("gemini", "ai_services", "Gemini AI"),
    ("anthropic", "ai_services", "Anthropic"),
    ("langchain", "ai_services", "LangChain"),
    ("huggingface", "ai_services", "HuggingFace"),
    ("tensorflow", "ai_services", "TensorFlow"),
    ("torch", "ai_services", "PyTorch"),
    # External APIs / Services
    ("stripe", "external_services", "Stripe"),
    ("twilio", "external_services", "Twilio"),
    ("sendgrid", "external_services", "SendGrid"),
    ("firebase", "external_services", "Firebase"),
    ("supabase", "external_services", "Supabase"),
    ("github", "external_services", "GitHub API"),
    ("gitlab", "external_services", "GitLab API"),
    # Cloud
    ("boto3", "external_services", "AWS SDK"),
    ("azure", "external_services", "Azure SDK"),
    ("google.cloud", "external_services", "GCP SDK"),
    # Container / infra
    ("docker", "infrastructure", "Docker"),
    ("kubernetes", "infrastructure", "Kubernetes"),
    ("nginx", "infrastructure", "Nginx"),
]

# Folder-name → layer hints
FOLDER_LAYER_MAP: dict[str, str] = {
    "frontend": "frontend",
    "client": "frontend",
    "ui": "frontend",
    "web": "frontend",
    "app": "frontend",
    "pages": "frontend",
    "views": "frontend",
    "components": "frontend",
    "api": "api_gateway",
    "routes": "api_gateway",
    "controllers": "controllers",
    "handlers": "controllers",
    "endpoints": "api_gateway",
    "services": "services",
    "service": "services",
    "usecases": "services",
    "domain": "services",
    "business": "services",
    "repositories": "repositories",
    "repository": "repositories",
    "repos": "repositories",
    "daos": "repositories",
    "models": "database",
    "schemas": "database",
    "migrations": "database",
    "db": "database",
    "database": "database",
    "auth": "auth",
    "authentication": "auth",
    "authorization": "auth",
    "middleware": "middleware",
    "cache": "cache",
    "queue": "message_queue",
    "workers": "message_queue",
    "jobs": "message_queue",
    "tasks": "message_queue",
    "storage": "storage",
    "upload": "storage",
    "ml": "ai_services",
    "ai": "ai_services",
    "nlp": "ai_services",
    "copilot": "ai_services",
    "infrastructure": "infrastructure",
    "infra": "infrastructure",
    "k8s": "infrastructure",
    "docker": "infrastructure",
}

# Canonical layer ordering (top → bottom)
LAYER_ORDER: list[str] = [
    "frontend",
    "api_gateway",
    "auth",
    "middleware",
    "controllers",
    "services",
    "repositories",
    "database",
    "cache",
    "message_queue",
    "storage",
    "ai_services",
    "external_services",
    "infrastructure",
]

LAYER_META: dict[str, dict] = {
    "frontend":          {"label": "Frontend",          "color": "#3b82f6", "icon": "monitor", "description": "User interface layer"},
    "api_gateway":       {"label": "API Gateway",       "color": "#8b5cf6", "icon": "server", "description": "HTTP API entry point"},
    "auth":              {"label": "Authentication",    "color": "#f59e0b", "icon": "shield", "description": "Identity & access control"},
    "middleware":        {"label": "Middleware",         "color": "#6b7280", "icon": "layers", "description": "Cross-cutting concerns"},
    "controllers":       {"label": "Controllers",       "color": "#ec4899", "icon": "cpu", "description": "Request handling logic"},
    "services":          {"label": "Business Services", "color": "#10b981", "icon": "zap", "description": "Core business logic"},
    "repositories":      {"label": "Repositories",      "color": "#06b6d4", "icon": "database", "description": "Data access patterns"},
    "database":          {"label": "Database",          "color": "#ef4444", "icon": "cylinder", "description": "Persistent data store"},
    "cache":             {"label": "Cache",              "color": "#f97316", "icon": "zap", "description": "High-speed data cache"},
    "message_queue":     {"label": "Message Queue",     "color": "#a78bfa", "icon": "mail", "description": "Async message passing"},
    "storage":           {"label": "Storage",           "color": "#64748b", "icon": "hard-drive", "description": "File & object storage"},
    "ai_services":       {"label": "AI Services",       "color": "#d946ef", "icon": "brain", "description": "Machine learning & AI"},
    "external_services": {"label": "External Services", "color": "#0ea5e9", "icon": "globe", "description": "Third-party integrations"},
    "infrastructure":    {"label": "Infrastructure",    "color": "#78716c", "icon": "box", "description": "Deployment & runtime"},
}


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class ArchNode:
    id: str
    layer: str
    label: str
    technologies: list[str] = field(default_factory=list)
    file_count: int = 0
    color: str = "#6b7280"
    icon: str = "box"
    description: str = ""
    position_x: float = 0.0
    position_y: float = 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "layer": self.layer,
            "label": self.label,
            "technologies": self.technologies,
            "file_count": self.file_count,
            "color": self.color,
            "icon": self.icon,
            "description": self.description,
            "position": {"x": self.position_x, "y": self.position_y},
        }


@dataclass
class ArchEdge:
    id: str
    source: str
    target: str
    label: str = ""
    edge_type: str = "depends_on"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source": self.source,
            "target": self.target,
            "label": self.label,
            "type": self.edge_type,
        }


@dataclass
class ArchitectureResult:
    nodes: list[ArchNode] = field(default_factory=list)
    edges: list[ArchEdge] = field(default_factory=list)
    detected_technologies: list[str] = field(default_factory=list)
    detected_layers: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "detected_technologies": self.detected_technologies,
            "detected_layers": self.detected_layers,
            "frameworks": self.frameworks,
            "languages": self.languages,
        }


# ── Inferrer ─────────────────────────────────────────────────────────────────

class ArchitectureInferrer:
    """
    Produces a high-level system architecture diagram from scan results.
    Uses folder structure, AST imports, API endpoints, and framework signals.
    """

    def infer(
        self,
        results: list[FileAnalysisResult],
        repo_languages: list[str],
        repo_frameworks: list[str],
        manifest_deps: list[str],
    ) -> ArchitectureResult:
        logger.info("Inferring architecture", files=len(results))

        layer_files: dict[str, list[str]] = {}       # layer → [file_paths]
        layer_techs: dict[str, set[str]] = {}         # layer → {tech labels}
        all_techs: set[str] = set()

        # ── Pass 1: folder-based layer detection ──────────────────────────────
        for result in results:
            path = result.file_path.replace("\\", "/")
            parts = list(PurePosixPath(path).parts)
            for part in parts[:-1]:  # skip filename itself
                layer = FOLDER_LAYER_MAP.get(part.lower())
                if layer:
                    layer_files.setdefault(layer, []).append(path)
                    break

        # ── Pass 2: import-based technology & layer detection ─────────────────
        for result in results:
            path = result.file_path.replace("\\", "/")
            all_imports = [imp.module.lower() for imp in result.imports]
            for sig, layer, tech in TECH_SIGNALS:
                if any(sig in imp for imp in all_imports):
                    layer_files.setdefault(layer, []).append(path)
                    layer_techs.setdefault(layer, set()).add(tech)
                    all_techs.add(tech)

        # ── Pass 3: manifest / framework signals ─────────────────────────────
        deps_lower = [d.lower() for d in manifest_deps]
        for sig, layer, tech in TECH_SIGNALS:
            if any(sig in dep for dep in deps_lower):
                layer_techs.setdefault(layer, set()).add(tech)
                all_techs.add(tech)
                # Ensure the layer exists even if no files mapped to it
                layer_files.setdefault(layer, [])

        # ── Pass 4: API endpoint detection → controllers layer ────────────────
        has_api_endpoints = any(len(r.api_endpoints) > 0 for r in results)
        if has_api_endpoints:
            for result in results:
                if result.api_endpoints:
                    path = result.file_path.replace("\\", "/")
                    layer_files.setdefault("controllers", []).append(path)

        # ── Pass 5: framework → layer hints ───────────────────────────────────
        for fw in repo_frameworks:
            fw_lower = fw.lower()
            for sig, layer, tech in TECH_SIGNALS:
                if sig in fw_lower:
                    layer_techs.setdefault(layer, set()).add(tech)
                    all_techs.add(tech)
                    layer_files.setdefault(layer, [])

        # ── Pass 6: language → implied layers ─────────────────────────────────
        for lang in repo_languages:
            ll = lang.lower()
            if ll in ("typescript", "javascript"):
                # If no explicit frontend but no backend either, assume frontend
                if not any(k in layer_files for k in ("api_gateway", "services")):
                    layer_files.setdefault("frontend", [])

        # ── Build nodes (only layers with evidence) ───────────────────────────
        active_layers = [l for l in LAYER_ORDER if l in layer_files]

        nodes: list[ArchNode] = []
        node_id_map: dict[str, str] = {}

        for idx, layer in enumerate(active_layers):
            meta = LAYER_META.get(layer, {"label": layer.title(), "color": "#6b7280", "icon": "box", "description": ""})
            techs = sorted(layer_techs.get(layer, set()))
            label = techs[0] if len(techs) == 1 else meta["label"]
            if techs and len(techs) > 1:
                label = f"{meta['label']}"

            node_id = f"arch_{layer}"
            node_id_map[layer] = node_id

            col_x = 400.0  # single column layout
            row_y = idx * 180.0

            nodes.append(ArchNode(
                id=node_id,
                layer=layer,
                label=label,
                technologies=techs,
                file_count=len(set(layer_files.get(layer, []))),
                color=meta["color"],
                icon=meta["icon"],
                description=meta["description"],
                position_x=col_x,
                position_y=row_y,
            ))

        # ── Build edges: sequential top-down ─────────────────────────────────
        edges: list[ArchEdge] = []
        for i in range(len(active_layers) - 1):
            src_layer = active_layers[i]
            tgt_layer = active_layers[i + 1]
            src_id = node_id_map[src_layer]
            tgt_id = node_id_map[tgt_layer]
            edge_id = f"{src_id}->{tgt_id}"
            edges.append(ArchEdge(
                id=edge_id,
                source=src_id,
                target=tgt_id,
                label="calls",
                edge_type="depends_on",
            ))

        # ── Build result ──────────────────────────────────────────────────────
        arch = ArchitectureResult(
            nodes=nodes,
            edges=edges,
            detected_technologies=sorted(all_techs),
            detected_layers=active_layers,
            frameworks=repo_frameworks,
            languages=repo_languages,
        )

        logger.info(
            "Architecture inferred",
            layers=len(nodes),
            edges=len(edges),
            technologies=len(all_techs),
        )
        return arch
