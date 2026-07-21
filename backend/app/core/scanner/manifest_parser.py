"""
Parses dependency manifest files to detect frameworks and collect dependency info.

Supported manifests:
  - package.json          (Node.js / JavaScript / TypeScript)
  - requirements.txt      (Python)
  - pyproject.toml        (Python modern)
  - pom.xml               (Java / Maven)
  - build.gradle          (Java / Gradle)
  - Dockerfile            (read-only — detect base image)
  - go.mod                (Go)
  - Cargo.toml            (Rust)
"""
import json
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

from app.utils.logger import get_logger

logger = get_logger(__name__)

# Maps dependency names → framework label
FRAMEWORK_SIGNALS: dict[str, str] = {
    # JavaScript / TypeScript
    "react": "React",
    "react-dom": "React",
    "next": "Next.js",
    "vue": "Vue",
    "@angular/core": "Angular",
    "express": "Express",
    "@nestjs/core": "NestJS",
    "svelte": "Svelte",
    "nuxt": "Nuxt",
    "remix": "Remix",
    "astro": "Astro",
    "tailwindcss": "Tailwind CSS",
    "vite": "Vite",
    "webpack": "Webpack",
    "@prisma/client": "Prisma",
    "mongoose": "Mongoose",
    "sequelize": "Sequelize",
    "typeorm": "TypeORM",
    "graphql": "GraphQL",
    "apollo-server": "Apollo",
    "socket.io": "Socket.IO",

    # Python
    "fastapi": "FastAPI",
    "django": "Django",
    "flask": "Flask",
    "starlette": "Starlette",
    "tornado": "Tornado",
    "sqlalchemy": "SQLAlchemy",
    "pydantic": "Pydantic",
    "celery": "Celery",
    "pytest": "pytest",
    "numpy": "NumPy",
    "pandas": "Pandas",
    "tensorflow": "TensorFlow",
    "torch": "PyTorch",
    "scikit-learn": "scikit-learn",
    "langchain": "LangChain",

    # Java
    "spring-boot-starter": "Spring Boot",
    "spring-core": "Spring",
    "hibernate-core": "Hibernate",
    "junit": "JUnit",
    "quarkus-core": "Quarkus",
    "micronaut-core": "Micronaut",

    # Go
    "gin-gonic/gin": "Gin",
    "labstack/echo": "Echo",
    "gorilla/mux": "Gorilla Mux",

    # Rust
    "actix-web": "Actix",
    "rocket": "Rocket",
    "tokio": "Tokio",
    "axum": "Axum",
}


@dataclass
class ManifestResult:
    frameworks: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    dev_dependencies: list[str] = field(default_factory=list)
    package_name: Optional[str] = None
    package_version: Optional[str] = None
    docker_base_image: Optional[str] = None
    raw_metadata: dict = field(default_factory=dict)


class ManifestParser:
    """
    Parses dependency manifests in a cloned repo root.
    Each parser method is isolated — failures in one don't affect others.
    """

    def parse(self, repo_path: Path) -> ManifestResult:
        """
        Scan the repo root for manifest files and return merged results.
        """
        result = ManifestResult()

        parsers = [
            (repo_path / "package.json",      self._parse_package_json),
            (repo_path / "requirements.txt",  self._parse_requirements_txt),
            (repo_path / "pyproject.toml",    self._parse_pyproject_toml),
            (repo_path / "pom.xml",           self._parse_pom_xml),
            (repo_path / "build.gradle",      self._parse_build_gradle),
            (repo_path / "go.mod",            self._parse_go_mod),
            (repo_path / "Cargo.toml",        self._parse_cargo_toml),
            (repo_path / "Dockerfile",        self._parse_dockerfile),
        ]

        for manifest_path, parser_fn in parsers:
            if manifest_path.exists():
                try:
                    parser_fn(manifest_path, result)
                except Exception as e:
                    logger.warning(
                        "Manifest parse error",
                        file=manifest_path.name,
                        error=str(e),
                    )

        result.frameworks = self._detect_frameworks(result.dependencies + result.dev_dependencies)
        return result

    # ── Parsers ────────────────────────────────────────────────────────────────

    def _parse_package_json(self, path: Path, result: ManifestResult) -> None:
        data = json.loads(path.read_text(encoding="utf-8"))
        result.package_name = data.get("name")
        result.package_version = data.get("version")
        result.dependencies.extend(data.get("dependencies", {}).keys())
        result.dev_dependencies.extend(data.get("devDependencies", {}).keys())
        result.raw_metadata["package_json"] = {
            "name": result.package_name,
            "version": result.package_version,
            "scripts": list(data.get("scripts", {}).keys()),
        }

    def _parse_requirements_txt(self, path: Path, result: ManifestResult) -> None:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith(("#", "-r", "--")):
                continue
            # Strip version specifiers: "fastapi>=0.111.0" → "fastapi"
            pkg = re.split(r"[>=<!~;\[\s]", line)[0].strip().lower()
            if pkg:
                result.dependencies.append(pkg)

    def _parse_pyproject_toml(self, path: Path, result: ManifestResult) -> None:
        content = path.read_text(encoding="utf-8")
        # Extract dependencies array from [project.dependencies] or [tool.poetry.dependencies]
        deps = re.findall(r'"([a-zA-Z0-9_\-]+)[>=<!~\[]?', content)
        result.dependencies.extend(d.lower() for d in deps)

    def _parse_pom_xml(self, path: Path, result: ManifestResult) -> None:
        content = path.read_text(encoding="utf-8")
        artifact_ids = re.findall(r"<artifactId>(.*?)</artifactId>", content)
        group_ids = re.findall(r"<groupId>(.*?)</groupId>", content)
        result.dependencies.extend(artifact_ids)
        # Spring Boot detection via groupId
        for gid in group_ids:
            if "springframework" in gid:
                result.dependencies.append("spring-core")

    def _parse_build_gradle(self, path: Path, result: ManifestResult) -> None:
        content = path.read_text(encoding="utf-8")
        # Match: implementation 'group:artifact:version'
        deps = re.findall(r"""['"]([\w.\-]+):([\w.\-]+):""", content)
        for _, artifact in deps:
            result.dependencies.append(artifact)

    def _parse_go_mod(self, path: Path, result: ManifestResult) -> None:
        content = path.read_text(encoding="utf-8")
        # require block or single-line requires
        requires = re.findall(r"require\s+([\w./\-]+)\s", content)
        block_requires = re.findall(r"^\s+([\w./\-]+)\s+v", content, re.MULTILINE)
        result.dependencies.extend(requires + block_requires)

    def _parse_cargo_toml(self, path: Path, result: ManifestResult) -> None:
        content = path.read_text(encoding="utf-8")
        # [dependencies] section entries: name = "version" or name = { version = "..." }
        deps = re.findall(r'^([a-zA-Z0-9_\-]+)\s*=', content, re.MULTILINE)
        result.dependencies.extend(deps)

    def _parse_dockerfile(self, path: Path, result: ManifestResult) -> None:
        content = path.read_text(encoding="utf-8")
        # First FROM line = base image
        match = re.search(r"^FROM\s+([^\s]+)", content, re.MULTILINE | re.IGNORECASE)
        if match:
            result.docker_base_image = match.group(1)
            result.raw_metadata["docker_base_image"] = result.docker_base_image

    # ── Framework detection ────────────────────────────────────────────────────

    def _detect_frameworks(self, all_deps: list[str]) -> list[str]:
        """Match dependency names against known framework signals."""
        deps_lower = {d.lower() for d in all_deps}
        detected = []
        seen = set()

        for dep, framework in FRAMEWORK_SIGNALS.items():
            if dep.lower() in deps_lower and framework not in seen:
                detected.append(framework)
                seen.add(framework)

        return detected
