from datetime import datetime, timedelta
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.parse import urlsplit

from celery import Celery
from sqlalchemy import select, delete

from .config import settings
from .db import SessionLocal, init_db
from .models import Transfer
from .utils import ensure_data_dirs, build_session, validate_target_url, filename_from_url, safe_filename, sha256_file, follow_safe_redirects

celery_app = Celery("cloudbell", broker=settings.celery_broker_url, backend=settings.celery_result_backend)
celery_app.conf.timezone = "UTC"
celery_app.conf.beat_schedule = {
    "cleanup-transfers": {
        "task": "app.tasks.cleanup_expired_files",
        "schedule": 60 * 60 * 24,
    }
}


def _update_transfer(transfer_id: int, **fields):
    db = SessionLocal()
    try:
        transfer = db.get(Transfer, transfer_id)
        if not transfer:
            return None
        for key, value in fields.items():
            setattr(transfer, key, value)
        db.commit()
        db.refresh(transfer)
        return transfer
    finally:
        db.close()


@celery_app.task(name="app.tasks.process_transfer")
def process_transfer(transfer_id: int):
    init_db()
    db = SessionLocal()
    downloads_dir = ensure_data_dirs()
    session = build_session()
    try:
        transfer = db.get(Transfer, transfer_id)
        if not transfer:
            return
        if transfer.status == "canceled":
            return
        transfer.status = "running"
        transfer.error_message = None
        db.commit()

        current_url = validate_target_url(transfer.source_url, allow_http=settings.download_allow_http)
        final_url, _history = follow_safe_redirects(session, current_url, settings.download_max_redirects)
        response = session.get(final_url, stream=True, allow_redirects=False, timeout=(settings.download_connect_timeout_seconds, settings.download_timeout_seconds))
        if response.is_redirect or response.is_permanent_redirect:
            raise ValueError("إعادة التوجيه النهائية غير مسموحة")
        content_length = response.headers.get("Content-Length")
        if content_length and int(content_length) > settings.max_download_bytes:
            raise ValueError("الملف يتجاوز الحد المسموح")
        content_type = response.headers.get("Content-Type")
        disposition = response.headers.get("Content-Disposition", "")
        name = filename_from_url(final_url)
        if "filename=" in disposition:
            name = safe_filename(disposition.split("filename=", 1)[1].strip(chr(34) + ";"))
        temp_path = None
        digest = None
        total = 0
        with NamedTemporaryFile(delete=False, dir=downloads_dir, prefix=f"transfer-{transfer.id}-", suffix=".part") as tmp:
            temp_path = Path(tmp.name)
            import hashlib
            hasher = hashlib.sha256()
            for chunk in response.iter_content(chunk_size=1024 * 256):
                if transfer.status == "canceled":
                    raise RuntimeError("تم إلغاء الطلب")
                if not chunk:
                    continue
                total += len(chunk)
                if total > settings.max_download_bytes:
                    raise ValueError("تم تجاوز الحد الأقصى للبيانات")
                tmp.write(chunk)
                hasher.update(chunk)
            digest = hasher.hexdigest()
        final_name = f"{transfer.id}_{safe_filename(name)}"
        name = safe_filename(disposition.split("filename=", 1)[1].strip('";'))
        temp_path.replace(final_path)
        transfer.status = "completed"
        name = safe_filename(disposition.split("filename=", 1)[1].strip('";'))
        transfer.stored_filename = final_name
        transfer.content_type = content_type
        transfer.sha256 = digest
        transfer.byte_size = total
        transfer.completed_at = datetime.utcnow()
        transfer.error_message = None
        db.commit()
    except Exception as exc:
        db.rollback()
        transfer = db.get(Transfer, transfer_id)
        if transfer and transfer.status != "canceled":
            transfer.status = "failed"
            transfer.error_message = str(exc)[:2000]
            db.commit()
        raise
    finally:
        session.close()
        db.close()


@celery_app.task(name="app.tasks.cleanup_expired_files")
def cleanup_expired_files():
    init_db()
    db = SessionLocal()
    downloads_dir = ensure_data_dirs()
    cutoff = datetime.utcnow() - timedelta(days=settings.cleanup_retention_days)
    try:
        rows = db.execute(select(Transfer).where(Transfer.completed_at.is_not(None), Transfer.completed_at < cutoff)).scalars().all()
        for transfer in rows:
            if transfer.stored_filename:
                path = downloads_dir / transfer.stored_filename
                if path.exists():
                    path.unlink()
            transfer.status = "expired"
            transfer.error_message = "انتهت مدة الاحتفاظ"
        db.commit()
    finally:
        db.close()
