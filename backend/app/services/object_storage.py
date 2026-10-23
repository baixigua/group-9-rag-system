"""MinIO 业务对象存储。

Milvus 也可使用同一个 MinIO 服务，但业务文档使用独立 bucket，避免与
Milvus 内部对象混放。所有同步 MinIO 调用都在线程池中执行，避免阻塞 FastAPI。
"""
from __future__ import annotations

import asyncio
import os
from pathlib import Path

from minio import Minio

from app.core.logger_handler import logger


class ObjectStorageService:
    def __init__(self) -> None:
        self._client: Minio | None = None

    @property
    def enabled(self) -> bool:
        return os.getenv("OBJECT_STORAGE_ENABLED", "false").lower() == "true"

    @property
    def bucket(self) -> str:
        return os.getenv("MINIO_DOCUMENTS_BUCKET", "rag-documents")

    def _get_client(self) -> Minio:
        if self._client is None:
            self._client = Minio(
                os.getenv("MINIO_ENDPOINT", "127.0.0.1:9000"),
                access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
                secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
                secure=os.getenv("MINIO_SECURE", "false").lower() == "true",
            )
        return self._client

    async def ensure_bucket(self) -> None:
        if not self.enabled:
            return
        client = self._get_client()
        exists = await asyncio.to_thread(client.bucket_exists, self.bucket)
        if not exists:
            await asyncio.to_thread(client.make_bucket, self.bucket)

    @staticmethod
    def build_object_key(doc_id: str, filename: str, user_id: str, kb_id: str | None) -> str:
        safe_name = Path(filename).name.replace("\\", "_").replace("/", "_")
        scope = f"kb/{kb_id}" if kb_id else f"personal/{user_id}"
        return f"{scope}/{doc_id}/{safe_name}"

    async def put_file(self, file_path: str, object_key: str, content_type: str | None = None) -> str:
        if not self.enabled:
            return ""
        await self.ensure_bucket()
        client = self._get_client()
        await asyncio.to_thread(
            client.fput_object,
            self.bucket,
            object_key,
            file_path,
            content_type=content_type or "application/octet-stream",
        )
        logger.info(f"[ObjectStorage] 已上传 {self.bucket}/{object_key}")
        return object_key

    async def delete(self, object_key: str | None) -> None:
        if not self.enabled or not object_key:
            return
        await asyncio.to_thread(self._get_client().remove_object, self.bucket, object_key)
        logger.info(f"[ObjectStorage] 已删除 {self.bucket}/{object_key}")


object_storage = ObjectStorageService()
