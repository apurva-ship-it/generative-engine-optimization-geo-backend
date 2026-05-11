from fastapi import APIRouter, HTTPException, status, Response, Depends, Request
from typing import List
from datetime import datetime

from .auth import _get_current_user_id

router = APIRouter(prefix="/v1/files")

files_db: dict[int, dict] = {
    1: {"name": "file1.txt", "deleted_at": None},
    2: {"name": "file2.txt", "deleted_at": None},
}

def _require_auth(request: Request):
    # raise if not authenticated
    _get_current_user_id(request)
    return True

@router.get("/", response_model=List[str])
async def list_files(_: bool = Depends(_require_auth)):
    return [f["name"] for f in files_db.values() if f["deleted_at"] is None]

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_file(_: bool = Depends(_require_auth)):
    # Returns a presigned URL for uploading a file (placeholder implementation)
    return {"presigned_url": "https://s3.amazonaws.com/bucket/file?signature"}

@router.get("/download/{file_id}")
async def download_file(file_id: int, _: bool = Depends(_require_auth)):
    file = files_db.get(file_id)
    if not file or file["deleted_at"] is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    # Return a presigned URL for downloading the file (placeholder implementation)
    return {"presigned_url": f"https://s3.amazonaws.com/bucket/{file['name']}?download_signature"}

@router.put("/{file_id}/content")
async def edit_content(file_id: int, _: bool = Depends(_require_auth)):
    return {"version_id": 42}

@router.delete("/{file_id}")
async def delete_file(file_id: int, _: bool = Depends(_require_auth)):
    file = files_db.get(file_id)
    if not file or file["deleted_at"] is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    file["deleted_at"] = datetime.utcnow()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
