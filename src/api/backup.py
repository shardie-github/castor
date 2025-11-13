"""
Backup API Endpoints

Provides endpoints for backup management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import Optional
from datetime import datetime
from pydantic import BaseModel

from src.backup import BackupManager
from src.tenants.tenant_isolation import get_current_tenant

router = APIRouter()


class BackupResponse(BaseModel):
    backup_id: str
    status: str
    backup_location: str
    backup_size_bytes: Optional[int] = None


@router.post("/create", response_model=BackupResponse)
async def create_backup(
    request: Request,
    tenant_id: str = Depends(get_current_tenant),
    backup_manager: BackupManager = Depends(lambda: request.app.state.backup_manager)
):
    """Create a backup"""
    backup_id = await backup_manager.create_daily_backup()
    
    backups = await backup_manager.list_backups(tenant_id=tenant_id)
    backup = next((b for b in backups if b["backup_id"] == backup_id), None)
    
    if not backup:
        raise HTTPException(status_code=500, detail="Backup creation failed")
    
    return BackupResponse(**backup)


@router.get("/list")
async def list_backups(
    request: Request,
    tenant_id: str = Depends(get_current_tenant),
    backup_manager: BackupManager = Depends(lambda: request.app.state.backup_manager)
):
    """List backups"""
    backups = await backup_manager.list_backups(tenant_id=tenant_id)
    return {"backups": backups}
