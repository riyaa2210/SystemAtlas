"""
Python code analyzer using Python's built-in ast module.
Extracts imports, functions, classes, API endpoints, DB calls, and HTTP calls.
"""
import ast
from pathlib import Path

from app.core.analyzer.base_analyzer import BaseAnalyzer
from app.core.analyzer.analysis_result import (
    FileAnalysisResult, FunctionInfo, ClassInfo,
    ImportInfo, ApiEndpointInfo, DatabaseCallInfo,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

ROUTE_DECORATORS = {"get", "post", "put", "delete", "patch", "route", "head", "options"}
DB_OPERATIONS = {
    "execute", "query", "filter", "filter_by", "all", "first", "one",
    "one_or_none", "scalar", "add", "delete", "commit", "rollback",
    "bulk_insert_mappings", "bulk_update_mappings", "merge",
}
HTTP_CLIENT_NAMES = {"requests", "httpx", "aiohttp", "urllib", "urllib2", "urllib3"}
HTTP_CLIENT_METHODS = {"get", "post", "put", "delete", "patch", "request", "head", "options", "fetch"}


class PythonAnalyzer(BaseAnalyzer):
    @property
    def supported_extensions(self) -> list[str]:
        return [".py"]

    def analyze_file(self, file_path: Path, repo_root: Path) -> FileAnalysisResult:
        relative_path = str(file_path.relative_to(repo_root))
        try:
            source = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            logger.warning("Cannot read Python file", file=relative_path, error=str(e))
            return FileAnalysisResult(file_path=relative_path, language="Python", lines_of_code=0, has_documentation=False)

        try:
            tree = ast.parse(source, filename=str(file_path))
        except SyntaxError as e:
            logger.warning("Syntax error in Python file", file=relative_path, error=str(e))
            return FileAnalysisResult(file_path=relative_path, language="Python", lines_of_code=len(source.splitlines()), has_documentation=False)

        visitor = _PythonVisitor()
        try:
            visitor.visit(tree)
        except Exception as e:
            logger.warning("AST visit failed", file=relative_path, error=str(e))

        return FileAnalysisResult(
            file_path=relative_path,
            language="Python",
            lines_of_code=len(source.splitlines()),
            has_documentation=bool(ast.get_docstring(tree)),
            imports=visitor.imports,
            classes=visitor.classes,
            functions=visitor.functions,
            api_endpoints=visitor.api_endpoints,
            db_calls=visitor.db_calls,
            http_calls=visitor.http_calls,
        )


class _PythonVisitor(ast.NodeVisitor):
    def __init__(self):
        self.imports: list[ImportInfo] = []
        self.classes: list[ClassInfo] = []
        self.functions: list[FunctionInfo] = []
        self.api_endpoints: list[ApiEndpointInfo] = []
        self.db_calls: list[DatabaseCallInfo] = []
        self.http_calls: list[str] = []
        self._http_aliases: set[str] = set()
        self._class_depth: int = 0

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.imports.append(ImportInfo(module=alias.name, names=[alias.asname or alias.name], is_relative=False))
            base = alias.name.split(".")[0]
            if base in HTTP_CLIENT_NAMES:
                self._http_aliases.add(alias.asname or alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        module = node.module or ""
        self.imports.append(ImportInfo(module=module, names=[alias.name for alias in node.names], is_relative=(node.level or 0) > 0))
        base = module.split(".")[0]
        if base in HTTP_CLIENT_NAMES:
            for alias in node.names:
                self._http_aliases.add(alias.asname or alias.name)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        methods = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append(FunctionInfo(name=item.name, line_start=item.lineno, line_end=item.end_lineno or item.lineno, is_async=isinstance(item, ast.AsyncFunctionDef), docstring=ast.get_docstring(item)))
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                parts, cur = [], base
                while isinstance(cur, ast.Attribute):
                    parts.append(cur.attr); cur = cur.value
                if isinstance(cur, ast.Name):
                    parts.append(cur.id)
                bases.append(".".join(reversed(parts)))
        self.classes.append(ClassInfo(name=node.name, line_start=node.lineno, line_end=node.end_lineno or node.lineno, methods=methods, bases=bases))
        self._class_depth += 1
        self.generic_visit(node)
        self._class_depth -= 1

    def visit_FunctionDef(self, node: ast.FunctionDef | ast.AsyncFunctionDef):
        if self._class_depth == 0:
            self.functions.append(FunctionInfo(name=node.name, line_start=node.lineno, line_end=node.end_lineno or node.lineno, is_async=isinstance(node, ast.AsyncFunctionDef), docstring=ast.get_docstring(node)))
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                func = decorator.func
                if isinstance(func, ast.Attribute) and func.attr.lower() in ROUTE_DECORATORS:
                    method = func.attr.upper()
                    path = ""
                    if decorator.args:
                        arg0 = decorator.args[0]
                        if isinstance(arg0, ast.Constant):
                            path = str(arg0.value)
                    methods_override = []
                    for kw in decorator.keywords:
                        if kw.arg == "methods" and isinstance(kw.value, ast.List):
                            for elt in kw.value.elts:
                                if isinstance(elt, ast.Constant):
                                    methods_override.append(str(elt.value).upper())
                    if methods_override:
                        for m in methods_override:
                            self.api_endpoints.append(ApiEndpointInfo(path=path, method=m, handler=node.name, line=node.lineno))
                    else:
                        self.api_endpoints.append(ApiEndpointInfo(path=path, method=method, handler=node.name, line=node.lineno))
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Call(self, node: ast.Call):
        self._detect_db_call(node)
        self._detect_http_call(node)
        self.generic_visit(node)

    def _detect_db_call(self, node: ast.Call):
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr not in DB_OPERATIONS:
            return
        table = None
        if node.args:
            arg0 = node.args[0]
            if isinstance(arg0, ast.Name): table = arg0.id
            elif isinstance(arg0, ast.Attribute): table = arg0.attr
            elif isinstance(arg0, ast.Constant) and isinstance(arg0.value, str): table = arg0.value
        self.db_calls.append(DatabaseCallInfo(operation=func.attr, table=table, line=node.lineno))

    def _detect_http_call(self, node: ast.Call):
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr.lower() not in HTTP_CLIENT_METHODS:
            return
        obj = func.value
        obj_name = obj.id if isinstance(obj, ast.Name) else (obj.attr if isinstance(obj, ast.Attribute) else "")
        if obj_name not in self._http_aliases and obj_name not in HTTP_CLIENT_NAMES:
            return
        url = ""
        if node.args:
            arg0 = node.args[0]
            if isinstance(arg0, ast.Constant) and isinstance(arg0.value, str): url = arg0.value
            elif isinstance(arg0, ast.Name): url = f"<{arg0.id}>"
            elif isinstance(arg0, ast.JoinedStr): url = "<f-string>"
        self.http_calls.append(f"{obj_name}.{func.attr}({url})")
