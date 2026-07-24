"""JavaScript/TypeScript analyzer using regex-based analysis."""
import re
from pathlib import Path
from app.core.analyzer.base_analyzer import BaseAnalyzer
from app.core.analyzer.analysis_result import FileAnalysisResult, FunctionInfo, ImportInfo, ApiEndpointInfo
from app.utils.logger import get_logger

logger = get_logger(__name__)

_RE_IMPORT_ES = re.compile(r'^\s*import\s+(?P<names>[^"\']+?)\s+from\s+["\'](?P<module>[^"\']+)["\']', re.MULTILINE)
_RE_IMPORT_CJS = re.compile(r'(?:const|let|var)\s+(?P<names>[\w\s{},*]+?)\s*=\s*require\s*\(\s*["\'](?P<module>[^"\']+)["\']\s*\)', re.MULTILINE)
_RE_IMPORT_SIDE = re.compile(r'^\s*import\s+["\'](?P<module>[^"\']+)["\']', re.MULTILINE)
_RE_EXPORT_FN = re.compile(r'^(?P<indent>\s*)export\s+(?P<async>async\s+)?function\s+(?P<name>\w+)\s*\(', re.MULTILINE)
_RE_EXPORT_CONST = re.compile(r'^(?P<indent>\s*)export\s+const\s+(?P<name>\w+)\s*=\s*(?:async\s+)?(?:function\s*\*?\s*\(|\([^)]*\)\s*=>|\w+\s*=>)', re.MULTILINE)
_RE_EXPORT_DEFAULT = re.compile(r'^(?P<indent>\s*)export\s+default\s+(?P<async>async\s+)?function\s+(?P<name>\w+)?\s*\(', re.MULTILINE)
_RE_EXPRESS = re.compile(r'(?:app|router|server)\s*\.\s*(?P<method>get|post|put|delete|patch|all|use)\s*\(\s*["\'](?P<path>[^"\']*)["\']', re.IGNORECASE | re.MULTILINE)
_RE_NEXTJS = re.compile(r'export\s+default\s+(?:async\s+)?function\s+(?P<name>\w+)', re.MULTILINE)
_RE_FETCH = re.compile(r'\bfetch\s*\(\s*(?P<url>["\'][^"\']*["\']|`[^`]*`)', re.MULTILINE)
_RE_AXIOS = re.compile(r'\baxios\s*(?:\.\s*(?P<method>get|post|put|delete|patch|request))?\s*\(\s*(?P<url>["\'][^"\']*["\']|`[^`]*`)?', re.MULTILINE)
_RE_JSDOC = re.compile(r'/\*\*')


def _line_of(source: str, pos: int) -> int:
    return source.count('\n', 0, pos) + 1


def _clean_names(raw: str) -> list[str]:
    names = []
    for group in re.findall(r'\{([^}]*)\}', raw):
        for part in group.split(','):
            part = part.strip()
            if ' as ' in part: part = part.split(' as ')[1].strip()
            if re.match(r'^\w+$', part): names.append(part)
    no_braces = re.sub(r'\{[^}]*\}', '', raw)
    for token in no_braces.split(','):
        token = token.strip()
        if token.startswith('* as '): names.append(token[5:].strip())
        elif re.match(r'^\w+$', token): names.append(token)
    return names or [raw.strip()]


class JsAnalyzer(BaseAnalyzer):
    @property
    def supported_extensions(self) -> list[str]:
        return [".js", ".jsx", ".ts", ".tsx"]

    def analyze_file(self, file_path: Path, repo_root: Path) -> FileAnalysisResult:
        relative_path = str(file_path.relative_to(repo_root))
        language = "TypeScript" if file_path.suffix in (".ts", ".tsx") else "JavaScript"
        try:
            source = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            logger.warning("Cannot read JS/TS file", file=relative_path, error=str(e))
            return FileAnalysisResult(file_path=relative_path, language=language, lines_of_code=0, has_documentation=False)
        try:
            return self._parse(source, relative_path, language)
        except Exception as e:
            logger.warning("JS/TS analysis failed", file=relative_path, error=str(e))
            return FileAnalysisResult(file_path=relative_path, language=language, lines_of_code=len(source.splitlines()), has_documentation=bool(_RE_JSDOC.search(source)))

    def _parse(self, source: str, relative_path: str, language: str) -> FileAnalysisResult:
        imports, functions, api_endpoints, http_calls = [], [], [], []

        for m in _RE_IMPORT_ES.finditer(source):
            imports.append(ImportInfo(module=m.group("module"), names=_clean_names(m.group("names")), is_relative=m.group("module").startswith(".")))
        for m in _RE_IMPORT_CJS.finditer(source):
            imports.append(ImportInfo(module=m.group("module"), names=_clean_names(m.group("names")), is_relative=m.group("module").startswith(".")))
        for m in _RE_IMPORT_SIDE.finditer(source):
            module = m.group("module")
            if not any(i.module == module for i in imports):
                imports.append(ImportInfo(module=module, names=[], is_relative=module.startswith(".")))

        for m in _RE_EXPORT_FN.finditer(source):
            functions.append(FunctionInfo(name=m.group("name"), line_start=_line_of(source, m.start()), line_end=_line_of(source, m.start()), is_async=bool(m.group("async"))))
        for m in _RE_EXPORT_CONST.finditer(source):
            functions.append(FunctionInfo(name=m.group("name"), line_start=_line_of(source, m.start()), line_end=_line_of(source, m.start()), is_async="async" in source[m.start():m.end()]))
        for m in _RE_EXPORT_DEFAULT.finditer(source):
            functions.append(FunctionInfo(name=m.group("name") or "default", line_start=_line_of(source, m.start()), line_end=_line_of(source, m.start()), is_async=bool(m.group("async"))))

        for m in _RE_EXPRESS.finditer(source):
            api_endpoints.append(ApiEndpointInfo(path=m.group("path"), method=m.group("method").upper(), handler=f"route:{m.group('path')}", line=_line_of(source, m.start())))

        if _RE_NEXTJS.search(source) and not api_endpoints:
            route_path = "/" + re.sub(r'\\', '/', relative_path)
            route_path = re.sub(r'\.(js|ts|jsx|tsx)$', '', route_path)
            route_path = re.sub(r'/index$', '', route_path)
            nm = _RE_NEXTJS.search(source)
            api_endpoints.append(ApiEndpointInfo(path=route_path, method="ANY", handler=nm.group("name") if nm else "handler", line=_line_of(source, nm.start()) if nm else 1))

        for m in _RE_FETCH.finditer(source):
            http_calls.append(f"fetch({m.group('url').strip(chr(34)+chr(39)+'`')})")
        for m in _RE_AXIOS.finditer(source):
            method = m.group("method") or "request"
            url = (m.group("url") or "").strip(chr(34)+chr(39)+'`') or "<dynamic>"
            http_calls.append(f"axios.{method}({url})")

        return FileAnalysisResult(file_path=relative_path, language=language, lines_of_code=len(source.splitlines()), has_documentation=bool(_RE_JSDOC.search(source)), imports=imports, functions=functions, api_endpoints=api_endpoints, http_calls=http_calls)
