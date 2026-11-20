"""Private object storage for original documents. Local-disk adapter; same interface as an S3 adapter."""
import hashlib
from pathlib import Path

from .config import get_settings


def _root() -> Path:
    p = Path(get_settings().storage_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p


def put(key: str, data: bytes) -> str:
    path = _root() / key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def get(key: str) -> bytes:
    path = (_root() / key).resolve()
    if _root().resolve() not in path.parents:
        raise PermissionError("invalid key")
    return path.read_bytes()
