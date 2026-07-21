"""Repository management endpoints."""
import uuid

from fastapi import APIRouter, HTTPException, BackgroundTasks, status

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
async def add_repository(
    request: AddRepositoryRequest,
    current_user: CurrentUser,
    db: DBSession,
):
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except UnauthorizedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except UnauthorizedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


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

        # Fire and forget — scan runs in background without blocking the response
        background_tasks.add_task(
            service.run_scan_pipeline,
            job_id=job.id,
            repo_id=repo_id,
        )
        return ScanJobResponse.model_validate(job)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except UnauthorizedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/{repo_id}/scan", response_model=list[ScanJobResponse])
async def list_scans(repo_id: uuid.UUID, current_user: CurrentUser, db: DBSession):
    repo_repo = RepoRepository(db)
    repo = await repo_repo.get_by_id(repo_id)
    if not repo or repo.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
    jobs = await repo_repo.get_scan_jobs(repo_id)
    return [ScanJobResponse.model_validate(j) for j in jobs]


@router.get("/{repo_id}/scan/{job_id}", response_model=ScanJobResponse)
async def get_scan(repo_id: uuid.UUID, job_id: uuid.UUID, current_user: CurrentUser, db: DBSession):
    repo_repo = RepoRepository(db)
    repo = await repo_repo.get_by_id(repo_id)
    if not repo or repo.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
    job = await repo_repo.get_scan_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan job not found")
    return ScanJobResponse.model_validate(job)
