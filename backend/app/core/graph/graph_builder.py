"""Converts FileAnalysisResult objects into Neo4j graph nodes and relationships."""
import hashlib
from pathlib import PurePosixPath
from app.core.analyzer.analysis_result import FileAnalysisResult
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _make_id(*parts: str) -> str:
    raw = "|".join(str(p) for p in parts)
    return hashlib.sha1(raw.encode()).hexdigest()[:16]


def _top_level_dir(file_path: str) -> str:
    parts = PurePosixPath(file_path.replace("\\", "/")).parts
    return parts[0] if len(parts) > 1 else "."


class GraphBuilder:
    async def build(self, repo_id: str, repo_name: str, results: list[FileAnalysisResult], neo4j_session) -> tuple[int, int]:
        logger.info("Building graph", repo_id=repo_id, files=len(results))
        nodes_created = 0
        edges_created = 0

        # Delete old graph
        await neo4j_session.run("MATCH (n {repo_id: $repo_id}) DETACH DELETE n", repo_id=repo_id)

        # Repository node
        repo_node_id = _make_id("repository", repo_id)
        await neo4j_session.run("MERGE (n:Repository {id: $id}) SET n += {name: $name, repo_id: $repo_id}", id=repo_node_id, name=repo_name, repo_id=repo_id)
        nodes_created += 1

        # Group by top-level dir → Module nodes
        module_map: dict[str, list[FileAnalysisResult]] = {}
        for r in results:
            module_map.setdefault(_top_level_dir(r.file_path), []).append(r)

        module_node_ids: dict[str, str] = {}
        for module_path, files in module_map.items():
            mid = _make_id("module", repo_id, module_path)
            module_node_ids[module_path] = mid
            await neo4j_session.run("MERGE (n:Module {id: $id}) SET n += {name: $name, path: $path, repo_id: $repo_id, file_count: $file_count}", id=mid, name=module_path, path=module_path, repo_id=repo_id, file_count=len(files))
            nodes_created += 1
            await neo4j_session.run("MATCH (repo:Repository {id: $rid}) MATCH (mod:Module {id: $mid}) MERGE (repo)-[:CONTAINS]->(mod)", rid=repo_node_id, mid=mid)
            edges_created += 1

        # File nodes
        file_path_to_node_id: dict[str, str] = {}
        for result in results:
            norm = result.file_path.replace("\\", "/")
            fid = _make_id("file", repo_id, norm)
            file_path_to_node_id[norm] = fid
            await neo4j_session.run("MERGE (n:File {id: $id}) SET n += {name: $name, path: $path, repo_id: $repo_id, language: $language, lines_of_code: $loc, has_documentation: $has_docs}", id=fid, name=PurePosixPath(norm).name, path=norm, repo_id=repo_id, language=result.language, loc=result.lines_of_code, has_docs=result.has_documentation)
            nodes_created += 1
            mid = module_node_ids[_top_level_dir(result.file_path)]
            await neo4j_session.run("MATCH (mod:Module {id: $mid}) MATCH (f:File {id: $fid}) MERGE (mod)-[:CONTAINS]->(f)", mid=mid, fid=fid)
            edges_created += 1

            # API nodes
            for ep in result.api_endpoints:
                aid = _make_id("api", repo_id, norm, ep.path, ep.method, ep.handler)
                await neo4j_session.run("MERGE (a:Api {id: $id}) SET a += {name: $name, path: $path, method: $method, repo_id: $repo_id, defined_in: $defined_in}", id=aid, name=ep.handler, path=ep.path, method=ep.method, repo_id=repo_id, defined_in=norm)
                nodes_created += 1
                await neo4j_session.run("MATCH (f:File {id: $fid}) MATCH (a:Api {id: $aid}) MERGE (f)-[:DEFINES]->(a)", fid=fid, aid=aid)
                edges_created += 1

        # Import edges
        for result in results:
            norm = result.file_path.replace("\\", "/")
            src_id = file_path_to_node_id[norm]
            src_dir = str(PurePosixPath(norm).parent)
            for imp in result.imports:
                tgt_id = self._resolve_import(imp.module, imp.is_relative, src_dir, file_path_to_node_id, result.language)
                if tgt_id and tgt_id != src_id:
                    await neo4j_session.run("MATCH (src:File {id: $sid}) MATCH (tgt:File {id: $tid}) MERGE (src)-[:IMPORTS]->(tgt)", sid=src_id, tid=tgt_id)
                    edges_created += 1

        logger.info("Graph built", repo_id=repo_id, nodes=nodes_created, edges=edges_created)
        return nodes_created, edges_created

    def _resolve_import(self, module: str, is_relative: bool, source_dir: str, path_map: dict, language: str) -> str | None:
        for candidate in self._candidates(module, is_relative, source_dir, language):
            if candidate in path_map:
                return path_map[candidate]
        return None

    def _candidates(self, module: str, is_relative: bool, source_dir: str, language: str) -> list[str]:
        m = module.replace("\\", "/").lstrip("/")
        candidates = []
        if language == "Python":
            base = f"{source_dir}/{m.replace('.', '/')}" if is_relative else m.replace(".", "/")
            candidates += [f"{base}.py", f"{base}/__init__.py"]
        elif language in ("JavaScript", "TypeScript"):
            base = f"{source_dir}/{m}" if is_relative else m
            base = str(PurePosixPath(base))
            for ext in (".ts", ".tsx", ".js", ".jsx"):
                candidates.append(f"{base}{ext}")
            candidates += [f"{base}/index.ts", f"{base}/index.js"]
        elif language == "Java":
            base = m.replace(".", "/")
            candidates += [f"{base}.java", f"src/main/java/{base}.java"]
        return candidates
