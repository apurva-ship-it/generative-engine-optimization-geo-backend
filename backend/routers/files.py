from fastapi import APIRouter, HTTPException, status, Response
from typing import List
from datetime import datetime

router = APIRouter(prefix="/v1/files")

files_db: dict[int, dict] = {
    1: {"name": "file1.txt", "deleted_at": None},
    2: {"name": "file2.txt", "deleted_at": None},
}

@router.get("/", response_model=List[str])
async def list_files():
    return [f["name"] for f in files_db.values() if f["deleted_at"] is None]

@router.post("/upload")
async def upload_file():
    return {"presigned_url": "https://s3.amazonaws.com/bucket/file?signature"}

@router.put("/{file_id}/content")
async def edit_content(file_id: int):
    return {"version_id": 42}

@router.delete("/{file_id}")
async def delete_file(file_id: int):
    file = files_db.get(file_id)
    if not file or file["deleted_at"] is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    file["deleted_at"] = datetime.utcnow()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
