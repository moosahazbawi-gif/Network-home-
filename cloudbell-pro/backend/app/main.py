from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from .auth import create_access_token, decode_token, hash_password, verify_password
from .config import settings
from .db import get_session, init_db
from .models import User, Transfer
from .schemas import (
    BootstrapRequest,
    LoginRequest,
    TokenResponse,
    TransferCreate,
    TransferOut,
    UserOut,
)
from .tasks import process_transfer
from .utils import ensure_data_dirs, validate_target_url

app = FastAPI(title=settings.app_name)
security = HTTPBearer(auto_error=False)


@app.on_event("startup")
def startup_event():
    import app.models  # noqa: F401
    ensure_data_dirs()
    init_db()


@app.get("/api/health")
def health(db: Session = Depends(get_session)):
    ok = True
    db.execute(select(1))
    return {"status": "ok", "service": settings.app_name, "database": ok}


def get_current_user(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)], db: Session = Depends(get_session)) -> User:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="غير مصرح")
    try:
        email = decode_token(credentials.credentials)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="رمز غير صالح")
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="المستخدم غير موجود")
    return user


@app.post("/api/auth/bootstrap-admin", response_model=UserOut)
def bootstrap_admin(payload: BootstrapRequest, db: Session = Depends(get_session)):
    if not settings.bootstrap_admin_email or not settings.bootstrap_admin_password:
        raise HTTPException(status_code=400, detail="تهيئة المسؤول غير مفعلة")
    existing = db.execute(select(User)).scalars().first()
    if existing:
        raise HTTPException(status_code=409, detail="يوجد مستخدم بالفعل")
    if payload.email.lower() != settings.bootstrap_admin_email.lower() or payload.password != settings.bootstrap_admin_password:
        raise HTTPException(status_code=400, detail="بيانات التهيئة غير مطابقة")
    user = User(email=payload.email.lower(), password_hash=hash_password(payload.password), is_admin=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/api/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_session)):
    user = db.execute(select(User).where(User.email == payload.email.lower())).scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="بيانات الدخول غير صحيحة")
    token = create_access_token(user.email)
    return TokenResponse(access_token=token)


@app.get("/api/auth/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@app.post("/api/transfers", response_model=TransferOut, status_code=201)
def create_transfer(payload: TransferCreate, db: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    try:
        url = validate_target_url(payload.url, allow_http=settings.download_allow_http)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    transfer = Transfer(user_id=current_user.id, source_url=url, status="queued")
    db.add(transfer)
    db.commit()
    db.refresh(transfer)
    process_transfer.delay(transfer.id)
    return transfer


@app.get("/api/transfers", response_model=list[TransferOut])
def list_transfers(db: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    rows = db.execute(select(Transfer).where(Transfer.user_id == current_user.id).order_by(Transfer.id.desc())).scalars().all()
    return rows


@app.get("/api/transfers/{transfer_id}", response_model=TransferOut)
def get_transfer(transfer_id: int, db: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    transfer = db.get(Transfer, transfer_id)
    if not transfer or transfer.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="الطلب غير موجود")
    return transfer


@app.post("/api/transfers/{transfer_id}/cancel", response_model=TransferOut)
def cancel_transfer(transfer_id: int, db: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    transfer = db.get(Transfer, transfer_id)
    if not transfer or transfer.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="الطلب غير موجود")
    if transfer.status in {"completed", "failed", "canceled", "expired"}:
        return transfer
    transfer.status = "canceled"
    transfer.error_message = "تم الإلغاء بواسطة المستخدم"
    db.commit()
    db.refresh(transfer)
    return transfer


@app.get("/api/transfers/{transfer_id}/file")
def download_file(transfer_id: int, db: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    transfer = db.get(Transfer, transfer_id)
    if not transfer or transfer.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="الملف غير موجود")
    if transfer.status != "completed" or not transfer.stored_filename:
        raise HTTPException(status_code=409, detail="الملف غير جاهز")
    path = ensure_data_dirs() / transfer.stored_filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="الملف مفقود")
    return FileResponse(path, filename=transfer.safe_filename or path.name, media_type=transfer.content_type or "application/octet-stream")
