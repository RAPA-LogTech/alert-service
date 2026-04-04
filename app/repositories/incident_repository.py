import json
from decimal import Decimal
from typing import Any

from ..core.aws_clients import get_dynamodb_resource, get_s3_client
from ..core.config import get_settings


class IncidentRepository:
    def __init__(self) -> None:
        settings = get_settings()
        ddb = get_dynamodb_resource()
        self._table = ddb.Table(settings.ddb_table_slack_messages)
        self._gsi_name = settings.ddb_gsi_status_created_at
        self._s3_bucket = settings.s3_bucket_slack_messages
        self._s3 = get_s3_client()

    def query_by_status(
        self,
        *,
        status: str,
        limit: int,
        exclusive_start_key: dict[str, Any] | None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
        params: dict[str, Any] = {
            "IndexName": self._gsi_name,
            "KeyConditionExpression": "#st = :status",
            "ExpressionAttributeNames": {"#st": "status"},
            "ExpressionAttributeValues": {":status": status},
            "ScanIndexForward": False,
            "Limit": limit,
        }
        if exclusive_start_key:
            params["ExclusiveStartKey"] = exclusive_start_key

        response = self._table.query(**params)
        return response.get("Items", []), response.get("LastEvaluatedKey")

    def get_by_id(self, incident_id: str) -> dict[str, Any] | None:
        response = self._table.get_item(Key={"incident_id": incident_id})
        return response.get("Item")

    def get_detail(self, s3_key: str) -> dict[str, Any]:
        if not self._s3_bucket:
            return {}

        response = self._s3.get_object(Bucket=self._s3_bucket, Key=s3_key)
        body = response["Body"].read().decode("utf-8")
        return json.loads(body)


def sanitize_ddb_item(value: Any) -> Any:
    if isinstance(value, list):
        return [sanitize_ddb_item(item) for item in value]
    if isinstance(value, dict):
        return {key: sanitize_ddb_item(item) for key, item in value.items()}
    if isinstance(value, Decimal):
        return int(value) if value % 1 == 0 else float(value)
    return value
