"""Repository management endpoints with real-time scan progress via SSE."""
import uuid
import asyncio
import json

from fastapi import APIRouter, HTTPException, BackgroundTasks, status
from fastapi.responses import StreamingResponse

from app.dependencies import CurrentUser, DBSession
from app.services.repository_service import RepositoryService
from app.repositories.repo_repository import RepoRepository
from app.schemas.repository import (
    AddRepositoryRequest, RepositoryResponse,
    RepositoryDetailResponse, ScanJobResponse,
)
from app.utils.exceptions import NotFoundError, UnauthorizedError, ExternalServiceError

router = APIRouter()


@router.get("", response_model=list[RepositoryResponse])
async def list_repositories(current_user: CurrentUser, db: DBSession):
    repo_repo = RepoRepository(db)
    repos = await repo_repo.get_user_repositories(current_user.id)
    return [RepositoryResponse.model_validate(r) for r in repos]


@router.post("", response_model=RepositoryResponse, status_code=status.HTTP_201_CREATED)
async def add_repository(request: AddRepositoryRequest, current_user: CurrentUser, db: DBSession):
    try:
        service = RepositoryService(db)
        repo = await service.add_repository(current_user.id, request.github_url)
        return RepositoryResponse.model_validate(repo)
    except ExternalServiceError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{repo_id}", response_model=RepositoryDetailResponse)
async def get_repository(repo_id: uuid.UUID, current_user: CurrentUser, db: DBSession):
    try:
        repo_repo = RepoRepository(db)
        repo = await repo_repo.get_by_id(repo_id)
        if not repo:
            raise NotFoundError("Repository", str(repo_id))
        if repo.user_id != current_user.id:
            raise UnauthorizedError("Access denied")
        latest_scan = await repo_repo.get_latest_scan_job(repo_id)
        result = RepositoryDetailResponse.model_validate(repo)
        result.latest_scan = ScanJobResponse.model_validate(latest_scan) if latest_scan else None
        return result
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except UnauthorizedError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{repo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_repository(repo_id: uuid.UUID, current_user: CurrentUser, db: DBSession):
    try:
        repo_repo = RepoRepository(db)
        repo = await repo_repo.get_by_id(repo_id)
        if not repo:
            raise NotFoundError("Repository", str(repo_id))
        if repo.user_id != current_user.id:
            raise UnauthorizedError("Access denied")
        await repo_repo.delete_repository(repo)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except UnauthorizedError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/{repo_id}/scan", response_model=ScanJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_scan(
    repo_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
    background_tasks: BackgroundTasks,
):
    try:
        service = RepositoryService(db)
        job = await service.trigger_scan(repo_id, current_user.id)
        background_tasks.add_task(service.run_scan_pipeline, job_id=job.id, repo_id=repo_id)
        return ScanJobResponse.model_validate(job)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except UnauthorizedError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/{repo_id}/scan/stream")
async def stream_scan_progress(repo_id: uuid.UUID, current_user: CurrentUser, db: DBSession):
    """
    Server-Sent Events endpoint for real-time scan progress.
    Frontend subscribes with EventSource — no polling needed.
    """
    repo_repo = RepoRepository(db)
    repo = await repo_repo.get_by_id(repo_id)
    if not repo or repo.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Repository not found")

    async def event_generator():
        last_stage = None
        last_status = None
        attempts = 0
        max_attempts = 150  # 5 minutes max

        while attempts < max_attempts:
            # Need a fresh session each poll since we're in a generator
            from app.db.postgres import AsyncSessionFactory
            async with AsyncSessionFactory() as fresh_db:
                fresh_repo = RepoRepository(fresh_db)
                job = await fresh_repo.get_latest_scan_job(repo_id)

            if job:
                current_stage  = job.stage
                current_status = job.status

                if current_stage != last_stage or current_status != last_status:
                    data = {
                        "status":        job.status,
                        "stage":         job.stage,
                        "files_scanned": job.files_scanned,
                        "nodes_created": job.nodes_created,
                        "edges_created": job.edges_created,
                        "error":         job.error_message,
                    }
                    yield f"data: {json.dumps(data)}\n\n"
                    last_stage  = current_stage
                    last_status = current_status

                if job.status in ("completed", "failed"):
                    yield "data: {\"status\": \"done\"}\n\n"
                    break

            await asyncio.sleep(2)
            attempts += 1

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.get("/{repo_id}/scan", response_model=list[ScanJobResponse])
async def list_scans(repo_id: uuid.UUID, current_user: CurrentUser, db: DBSession):
    repo_repo = RepoRepository(db)
    repo = await repo_repo.get_by_id(repo_id)
    if not repo or repo.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Repository not found")
    jobs = await repo_repo.get_scan_jobs(repo_id)
    return [ScanJobResponse.model_validate(j) for j in jobs]


@router.get("/{repo_id}/scan/{job_id}", response_model=ScanJobResponse)
async def get_scan(repo_id: uuid.UUID, job_id: uuid.UUID, current_user: CurrentUser, db: DBSession):
    repo_repo = RepoRepository(db)
    repo = await repo_repo.get_by_id(repo_id)
    if not repo or repo.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Repository not found")
    job = await repo_repo.get_scan_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Scan job not found")
    return ScanJobResponse.model_validate(job)
