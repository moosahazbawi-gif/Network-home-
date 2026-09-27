from pathlib import Path
from typing import Annotated
import hashlib
from tempfile import NamedTemporaryFile
from datetime import datetime
from fastapi import Depends, FastAPI, HTTPException, status, UploadFile, File
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from .auth import create_access_token, decode_token, hash_password, verify_password
from .config import settings
from .db import get_session, init_db
from .models import User, Transfer, Upload
from .schemas import BootstrapRequest, LoginRequest, TokenResponse, TransferCreate, TransferOut, UserOut, UploadOut
from .tasks import process_transfer
from .utils import ensure_data_dirs, validate_target_url, safe_filename

app=FastAPI(title=settings.app_name)
security=HTTPBearer(auto_error=False)

@app.on_event("startup")
def startup_event():
    ensure_data_dirs(); init_db()

@app.get("/api/health")
def health(db: Session=Depends(get_session)):
    db.execute(select(1)); return {"status":"ok","service":settings.app_name,"database":True}

def get_current_user(credentials: Annotated[HTTPAuthorizationCredentials|None,Depends(security)],db: Session=Depends(get_session))->User:
    if not credentials or credentials.scheme.lower()!="bearer": raise HTTPException(401,"غير مصرح")
    try: email=decode_token(credentials.credentials)
    except Exception: raise HTTPException(401,"رمز غير صالح")
    user=db.execute(select(User).where(User.email==email)).scalar_one_or_none()
    if not user: raise HTTPException(401,"المستخدم غير موجود")
    return user

@app.post("/api/auth/bootstrap-admin",response_model=UserOut)
def bootstrap_admin(payload:BootstrapRequest,db:Session=Depends(get_session)):
    if not settings.bootstrap_admin_email or not settings.bootstrap_admin_password: raise HTTPException(400,"تهيئة المسؤول غير مفعلة")
    if db.execute(select(User.id)).first(): raise HTTPException(409,"يوجد مستخدم بالفعل")
    if payload.email.lower()!=settings.bootstrap_admin_email.lower() or payload.password!=settings.bootstrap_admin_password: raise HTTPException(400,"بيانات التهيئة غير مطابقة")
    user=User(email=payload.email.lower(),password_hash=hash_password(payload.password),is_admin=True); db.add(user); db.commit(); db.refresh(user); return user

@app.post("/api/auth/login",response_model=TokenResponse)
def login(payload:LoginRequest,db:Session=Depends(get_session)):
    user=db.execute(select(User).where(User.email==payload.email.lower())).scalar_one_or_none()
    if not user or not verify_password(payload.password,user.password_hash): raise HTTPException(401,"بيانات الدخول غير صحيحة")
    return TokenResponse(access_token=create_access_token(user.email))

@app.get("/api/auth/me",response_model=UserOut)
def me(current_user:User=Depends(get_current_user)): return current_user

@app.post("/api/transfers",response_model=TransferOut,status_code=201)
def create_transfer(payload:TransferCreate,db:Session=Depends(get_session),current_user:User=Depends(get_current_user)):
    active=db.execute(select(func.count(Transfer.id)).where(Transfer.user_id==current_user.id,Transfer.status.in_({"queued","running"}))).scalar_one()
    if active>=settings.max_active_transfers_per_user: raise HTTPException(429,"تم بلوغ الحد الأقصى للتنزيلات النشطة")
    try: url=validate_target_url(payload.url,allow_http=settings.download_allow_http)
    except ValueError as exc: raise HTTPException(400,str(exc))
    transfer=Transfer(user_id=current_user.id,source_url=url,status="queued"); db.add(transfer); db.commit(); db.refresh(transfer); process_transfer.delay(transfer.id); return transfer

@app.post("/api/uploads",response_model=UploadOut,status_code=201)
def create_upload(file:UploadFile=File(...),db:Session=Depends(get_session),current_user:User=Depends(get_current_user)):
    stored=db.execute(select(func.count(Upload.id)).where(Upload.user_id==current_user.id,Upload.status=="completed")).scalar_one()
    if stored>=settings.max_stored_files_per_user: raise HTTPException(429,"تم بلوغ الحد الأقصى للملفات المخزنة")
    name=safe_filename(file.filename or "upload.bin")
    target_dir=ensure_data_dirs(); temp_path=None; total=0; digest=hashlib.sha256()
    try:
        with NamedTemporaryFile(delete=False,dir=target_dir,prefix="upload-",suffix=".part") as tmp:
            temp_path=Path(tmp.name)
            while True:
                chunk=file.file.read(1024*1024)
                if not chunk: break
                total+=len(chunk)
                if total>settings.max_file_bytes: raise HTTPException(413,"الملف يتجاوز الحد الأقصى")
                tmp.write(chunk); digest.update(chunk)
        if total<settings.min_file_bytes:
            raise HTTPException(413,"الملف أصغر من الحد الأدنى")
        stored_name=f"upload_{current_user.id}_{int(datetime.utcnow().timestamp()*1000000)}_{name}"
        final_path=target_dir/stored_name
        temp_path.replace(final_path); temp_path=None
        upload=Upload(user_id=current_user.id,safe_filename=name,stored_filename=stored_name,content_type=file.content_type,sha256=digest.hexdigest(),byte_size=total,status="completed",completed_at=datetime.utcnow())
        db.add(upload); db.commit(); db.refresh(upload)
        return upload
    except HTTPException:
        db.rollback()
        if temp_path and temp_path.exists(): temp_path.unlink(missing_ok=True)
        raise
    except Exception as exc:
        db.rollback()
        if temp_path and temp_path.exists(): temp_path.unlink(missing_ok=True)
        if 'final_path' in locals() and final_path.exists():
            final_path.unlink(missing_ok=True)
        raise HTTPException(500,f"فشل رفع الملف: {str(exc)[:200]}")
    finally:
        file.file.close()

@app.get("/api/uploads",response_model=list[UploadOut])
def list_uploads(db:Session=Depends(get_session),current_user:User=Depends(get_current_user)):
    return db.execute(select(Upload).where(Upload.user_id==current_user.id).order_by(Upload.id.desc())).scalars().all()

@app.get("/api/uploads/{upload_id}/file")
def download_upload(upload_id:int,db:Session=Depends(get_session),current_user:User=Depends(get_current_user)):
    upload=db.get(Upload,upload_id)
    if not upload or upload.user_id!=current_user.id or upload.status!="completed" or not upload.stored_filename: raise HTTPException(404,"الملف غير موجود")
    path=(ensure_data_dirs()/upload.stored_filename).resolve(); root=ensure_data_dirs().resolve()
    if not path.is_file() or root not in path.parents: raise HTTPException(404,"الملف مفقود")
    return FileResponse(path,filename=upload.safe_filename,media_type=upload.content_type or "application/octet-stream")

@app.delete("/api/uploads/{upload_id}",status_code=204)
def delete_upload(upload_id:int,db:Session=Depends(get_session),current_user:User=Depends(get_current_user)):
    upload=db.get(Upload,upload_id)
    if not upload or upload.user_id!=current_user.id: raise HTTPException(404,"الملف غير موجود")
    if upload.stored_filename:
        path=ensure_data_dirs()/upload.stored_filename
        path.unlink(missing_ok=True)
    db.delete(upload); db.commit()

@app.get("/api/transfers",response_model=list[TransferOut])
def list_transfers(db:Session=Depends(get_session),current_user:User=Depends(get_current_user)):
    return db.execute(select(Transfer).where(Transfer.user_id==current_user.id).order_by(Transfer.id.desc())).scalars().all()

@app.get("/api/transfers/{transfer_id}",response_model=TransferOut)
def get_transfer(transfer_id:int,db:Session=Depends(get_session),current_user:User=Depends(get_current_user)):
    transfer=db.get(Transfer,transfer_id)
    if not transfer or transfer.user_id!=current_user.id: raise HTTPException(404,"الطلب غير موجود")
    return transfer

@app.post("/api/transfers/{transfer_id}/cancel",response_model=TransferOut)
def cancel_transfer(transfer_id:int,db:Session=Depends(get_session),current_user:User=Depends(get_current_user)):
    transfer=db.get(Transfer,transfer_id)
    if not transfer or transfer.user_id!=current_user.id: raise HTTPException(404,"الطلب غير موجود")
    if transfer.status in {"completed","failed","canceled","expired"}: return transfer
    transfer.status="canceled"; transfer.error_message="تم الإلغاء بواسطة المستخدم"; db.commit(); db.refresh(transfer); return transfer

@app.get("/api/transfers/{transfer_id}/file")
def download_file(transfer_id:int,db:Session=Depends(get_session),current_user:User=Depends(get_current_user)):
    transfer=db.get(Transfer,transfer_id)
    if not transfer or transfer.user_id!=current_user.id or transfer.status!="completed" or not transfer.stored_filename: raise HTTPException(404,"الملف غير موجود")
    path=(ensure_data_dirs()/transfer.stored_filename).resolve(); root=ensure_data_dirs().resolve()
    if not path.is_file() or root not in path.parents: raise HTTPException(404,"الملف مفقود")
    return FileResponse(path,filename=transfer.safe_filename or path.name,media_type=transfer.content_type or "application/octet-stream")
