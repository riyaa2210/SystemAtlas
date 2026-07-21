"""Java code analyzer using regex-based analysis."""
import re
from pathlib import Path
from app.core.analyzer.base_analyzer import BaseAnalyzer
from app.core.analyzer.analysis_result import FileAnalysisResult, ClassInfo, FunctionInfo, ImportInfo, ApiEndpointInfo
from app.utils.logger import get_logger

logger = get_logger(__name__)

_RE_IMPORT = re.compile(r'^\s*import\s+(?:static\s+)?(?P<module>[\w.]+)\s*;', re.MULTILINE)
_RE_CLASS = re.compile(r'^\s*(?:(?:public|protected|private|abstract|final|\s)*\s+)?(?:class|interface|enum|record)\s+(?P<name>\w+)(?:\s+extends\s+(?P<extends>[\w<>, ]+?))?(?:\s+implements\s+(?P<implements>[\w<>, ]+?))?\s*(?:\{|$)', re.MULTILINE)
_RE_METHOD = re.compile(r'^\s*(?:(?:public|protected|private|static|final|abstract|synchronized|native|default)\s+)*(?P<return_type>[\w<>\[\],\s.]+?)\s+(?P<name>[a-z]\w*)\s*\((?P<params>[^)]*)\)\s*(?:throws\s+[\w<>, ]+\s*)?(?:\{|;)', re.MULTILINE)
_RE_SPRING_MAPPING = re.compile(r'@(?P<type>GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping|RequestMapping)\s*(?:\(\s*(?:value\s*=\s*)?["\'](?P<path>[^"\']*)["\'](?:[^)]*))?\s*\)', re.MULTILINE)
_RE_METHOD_NAME = re.compile(r'(?:public|protected|private|static|final|\s)+[\w<>\[\],\s.]+\s+(?P<name>\w+)\s*\(', re.MULTILINE)
_RE_JAVADOC = re.compile(r'/\*\*')
_JAVA_KW = {"if", "for", "while", "switch", "catch", "return", "new", "throw", "try", "else", "do"}

_SPRING_METHOD_MAP = {"GetMapping": "GET", "PostMapping": "POST", "PutMapping": "PUT", "DeleteMapping": "DELETE", "PatchMapping": "PATCH", "RequestMapping": "ANY"}


def _line_of(source: str, offset: int) -> int:
    return source.count('\n', 0, offset) + 1


class JavaAnalyzer(BaseAnalyzer):
    @property
    def supported_extensions(self) -> list[str]:
        return [".java"]

    def analyze_file(self, file_path: Path, repo_root: Path) -> FileAnalysisResult:
        relative_path = str(file_path.relative_to(repo_root))
        try:
            source = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            logger.warning("Cannot read Java file", file=relative_path, error=str(e))
            return FileAnalysisResult(file_path=relative_path, language="Java", lines_of_code=0, has_documentation=False)
        try:
            return self._parse(source, relative_path)
        except Exception as e:
            logger.warning("Java analysis failed", file=relative_path, error=str(e))
            return FileAnalysisResult(file_path=relative_path, language="Java", lines_of_code=len(source.splitlines()), has_documentation=bool(_RE_JAVADOC.search(source)))

    def _parse(self, source: str, relative_path: str) -> FileAnalysisResult:
        imports, classes, api_endpoints = [], [], []

        for m in _RE_IMPORT.finditer(source):
            module = m.group("module")
            parts = module.rsplit(".", 1)
            imports.append(ImportInfo(module=module, names=[parts[-1]], is_relative=False))

        for m in _RE_CLASS.finditer(source):
            class_name = m.group("name")
            line_start = _line_of(source, m.start())
            bases = []
            for attr in ("extends", "implements"):
                if m.group(attr):
                    for b in m.group(attr).split(","):
                        b = re.sub(r'<.*>', '', b).strip()
                        if b: bases.append(b)

            body_start = source.find('{', m.start())
            if body_start == -1: body_start = m.end()
            next_class = _RE_CLASS.search(source, m.end())
            body_end = next_class.start() if next_class else len(source)
            class_body = source[body_start:body_end]

            methods = []
            for mm in _RE_METHOD.finditer(class_body):
                name = mm.group("name")
                if name in _JAVA_KW: continue
                methods.append(FunctionInfo(name=name, line_start=_line_of(source, body_start + mm.start()), line_end=_line_of(source, body_start + mm.start()), is_async=False))

            classes.append(ClassInfo(name=class_name, line_start=line_start, line_end=_line_of(source, body_end), methods=methods, bases=bases))

        for m in _RE_SPRING_MAPPING.finditer(source):
            path = m.group("path") or "/"
            http_method = _SPRING_METHOD_MAP.get(m.group("type"), "ANY")
            handler_name = "unknown"
            hs = _RE_METHOD_NAME.search(source, m.end())
            if hs and (hs.start() - m.end()) < 300:
                handler_name = hs.group("name")
            api_endpoints.append(ApiEndpointInfo(path=path, method=http_method, handler=handler_name, line=_line_of(source, m.start())))

        return FileAnalysisResult(file_path=relative_path, language="Java", lines_of_code=len(source.splitlines()), has_documentation=bool(_RE_JAVADOC.search(source)), imports=imports, classes=classes, api_endpoints=api_endpoints)
