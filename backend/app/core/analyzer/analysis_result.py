"""
Shared data models for analysis results.
These are pure dataclasses with no framework dependencies.
"""
from dataclasses import dataclass, field


@dataclass
class FunctionInfo:
    name: str
    line_start: int
    line_end: int
    is_async: bool = False
    docstring: str | None = None


@dataclass
class ClassInfo:
    name: str
    line_start: int
    line_end: int
    methods: list[FunctionInfo] = field(default_factory=list)
    bases: list[str] = field(default_factory=list)


@dataclass
class ImportInfo:
    module: str
    names: list[str] = field(default_factory=list)
    is_relative: bool = False


@dataclass
class ApiEndpointInfo:
    path: str
    method: str       # GET | POST | PUT | DELETE | PATCH
    handler: str      # function/method name
    line: int


@dataclass
class DatabaseCallInfo:
    operation: str    # SELECT | INSERT | UPDATE | DELETE | query | execute
    table: str | None
    line: int


@dataclass
class FileAnalysisResult:
    """Complete analysis result for a single file."""
    file_path: str              # relative to repo root
    language: str
    lines_of_code: int
    has_documentation: bool
    imports: list[ImportInfo] = field(default_factory=list)
    classes: list[ClassInfo] = field(default_factory=list)
    functions: list[FunctionInfo] = field(default_factory=list)
    api_endpoints: list[ApiEndpointInfo] = field(default_factory=list)
    db_calls: list[DatabaseCallInfo] = field(default_factory=list)
    http_calls: list[str] = field(default_factory=list)   # URLs or client calls
