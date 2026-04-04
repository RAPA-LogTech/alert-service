from functools import lru_cache

import boto3
from botocore.client import BaseClient
from boto3.resources.base import ServiceResource

from .config import get_settings


@lru_cache
def get_dynamodb_resource() -> ServiceResource:
    settings = get_settings()
    return boto3.resource("dynamodb", region_name=settings.aws_region)


@lru_cache
def get_s3_client() -> BaseClient:
    settings = get_settings()
    return boto3.client("s3", region_name=settings.aws_region)
