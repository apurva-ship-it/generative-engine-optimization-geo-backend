"""
FastAPI router for generating presigned S3 URLs.

Uses boto3 to create a PUT URL for upload and a GET URL for access.
The URLs are valid for 5 minutes.
"""

from datetime import datetime, timedelta
from typing import Dict

import boto3
from botocore.exceptions import BotoCoreError, NoCredentialsError
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..config import Settings

router = APIRouter(prefix="/api/v1/presigned", tags=["presigned"])


class PresignedRequest(BaseModel):
    object_name: str

    model_config = {"extra": "forbid"}


class PresignedResponse(BaseModel):
    put_url: str
    get_url: str

    model_config = {"from_attributes": True}


@router.post("/url", response_model=PresignedResponse)
async def generate_presigned_url(
    req: PresignedRequest,
    settings: Settings = Depends(),
):
    """Generate a presigned PUT and GET URL for the given S3 object name.

    Expects AWS credentials to be available via environment variables
    (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN if needed).
    """
    s3_kwargs = {
        "region_name": settings.aws_region,
        "endpoint_url": settings.aws_endpoint_url,
    }
    try:
        s3 = boto3.client("s3", **s3_kwargs)
    except (BotoCoreError, NoCredentialsError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to initialize S3 client",
        ) from exc

    expiration = int(timedelta(minutes=5).total_seconds())
    try:
        put_url = s3.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": settings.aws_bucket_name,
                "Key": req.object_name,
            },
            ExpiresIn=expiration,
            HttpMethod="PUT",
        )
        get_url = s3.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": settings.aws_bucket_name,
                "Key": req.object_name,
            },
            ExpiresIn=expiration,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate presigned URLs",
        ) from exc

    return PresignedResponse(put_url=put_url, get_url=get_url)

"""End of presigned router."""
